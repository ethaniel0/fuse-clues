import os
import yaml
from engine.file_config import DirectoryMap, FileConfig
from engine import conditions
from engine import actions
from engine.rules import Rule

ref_folder = os.path.dirname(os.path.realpath(__file__))

def parse_condition(cond_dict) -> conditions.Condition:

    if isinstance(cond_dict, str):
        if cond_dict == 'always':
            return conditions.AlwaysCondition()
    elif isinstance(cond_dict, dict):
        if len(cond_dict) != 1:
            raise ValueError(f"Condition dict should have exactly one key, got: {cond_dict}")
        name, value = next(iter(cond_dict.items()))
        if name == 'all':
            return conditions.AllCondition(conditions=[parse_condition(c) for c in value])
        elif name == 'any':
            return conditions.AnyCondition(conditions=[parse_condition(c) for c in value])
        elif name == 'not':
            return conditions.NotCondition(condition=parse_condition(value))
        if name == 'file_exists':
            return conditions.FileExistsCondition(path=value)
        elif name == 'dir_exists':
            return conditions.DirExistsCondition(path=value)
        elif name == 'file_content_matches':
            path = value['path']
            expected_content = value['expected_content']
            return conditions.FileContentMatchesCondition(path=path, expected_content=expected_content)
        elif name == 'file_content_contains':
            path = value['path']
            expected_substring = value['expected_substring']
            return conditions.FileContentContainsCondition(path=path, expected_content=expected_substring)
        elif name == 'attribute_equals':
            attr = value['attribute']
            val = value['value']
            return conditions.NodeAttributeEqualsCondition(attribute=attr, value=val)
        elif name == 'permissions_equals':
            return conditions.PermissionCondition( path=value['path'], required_perms=value['permissions'] )
        elif name == 'can_access':
            return conditions.PermissionRelativeToUserCondition(can_read=value)
        
        elif name == 'offset':
            offset = value['threshold']
            mode = value.get('mode', 'gte')
            if mode not in ('lt', 'lte', 'eq', 'neq', 'gte', 'gt'):
                raise ValueError(f"Invalid offset condition mode: {mode}")
            return conditions.OffsetCondition(offset=offset, mode=mode)
        elif name == 'size':
            size = value['threshold']
            mode = value.get('mode', 'gte')
            if mode not in ('lt', 'lte', 'eq', 'neq', 'gte', 'gt'):
                raise ValueError(f"Invalid size condition mode: {mode}")
            return conditions.SizeCondition(size=size, mode=mode)
        elif name == 'file_size':
            path = value['path']
            size = value['threshold']
            mode = value.get('mode', 'gte')
            if mode not in ('lt', 'lte', 'eq', 'neq', 'gte', 'gt'):
                raise ValueError(f"Invalid size condition mode: {mode}")
            return conditions.FileSizeCondition(path=path, size=size, mode=mode)
        
    raise ValueError(f"Unknown condition type: {name}, for {cond_dict}")

def parse_action(action_dict) -> actions.Action:
    if len(action_dict) != 1:
        raise ValueError(f"Action dict should have exactly one key, got: {action_dict}")
    name, value = next(iter(action_dict.items()))
    if name == 'value':
        return actions.SetValueAction(value=value)
    elif name == 'value_eval':
        return actions.SetValueEvalAction(eval_str=value)
    elif name == 'write_attribute':
        attr = value['attribute']
        val = value['value']
        return actions.WriteAttributeAction(attribute=attr, value=val)
    elif name == 'content_text':
        return actions.ReadWriteContentTextAction(content_str=value)
    elif name == 'content_file':
        return actions.ReadWriteContentFileAction(content_filename=value)
    elif name == 'eval_value':
        return actions.ReadWriteContentEvalAction(eval_str=value)
    elif name == 'map_to':
        return actions.MapToEntityAction(target_path=value)
    elif name == 'error':
        return actions.ErrorAction(error=value)
    else:
        raise ValueError(f"Unknown action type: {name}")

def parse_config_file(filename: str) -> FileConfig:
    try:
        with open(os.path.join(ref_folder, filename), 'r') as f:
            config_dict = yaml.safe_load(f)
        
        hooks: dict[str, list[Rule]] = {}
        for hook_name, rules in config_dict.get('hooks', {}).items():
            hooks[hook_name] = []
            for rule_dict in rules:
                condition = parse_condition(rule_dict['condition'])
                actions = [parse_action(a) for a in rule_dict['actions']]
                hooks[hook_name].append(Rule(condition=condition, actions=actions))

        directory_map = config_dict.get('directory_map', None)
        if directory_map:
            condition = parse_condition(directory_map['condition'])
            map_dir = directory_map['map_to']
            directory_map = DirectoryMap(condition, map_dir)

        return FileConfig(hooks=hooks, directory_map=directory_map)
    except Exception as e:
        print(f"Error parsing config file {filename}: {e}")
        # print trace
        import traceback
        traceback.print_exc()
        return None
import os
import pathlib
import mfusepy as fuse
import errno
from fuse_tricks.file_config import FileConfig
from fuse_tricks.config_parser import parse_config_file
from typing import Callable, Any

def get_config_file(path: str) -> FileConfig | None:
    config_path = path + "_config.yaml"
    if os.path.isfile(config_path):
        return parse_config_file(config_path)
    return None

def get_config_path(path: str, check_exists: bool=True) -> str | None:
    config_path = path + "_config.yaml"
    if not check_exists:
        return config_path
    if os.path.isfile(config_path):
        return config_path
    return None

def config_file_has_related_entity(config_path: str) -> bool:
    file_path = config_path.removesuffix("_config.yaml")
    return os.path.isfile(file_path) or os.path.isdir(file_path)

def map_to_path(original_path: str, new_path: str, root_path: str):
    # if new_path is absolute, return it relative to root path
    if os.path.isabs(new_path):
        return os.path.join(root_path, new_path.lstrip('/'))
    # otherwise, return it relative to original path's parent
    return os.path.join(os.path.dirname(original_path), new_path)

def get_real_path(path: str, root_path: str) -> str:
    rel_parts = os.path.relpath(path, root_path).split(os.sep)

    if rel_parts == ['.']:
        return root_path
    if len(rel_parts) == 1: # is last child
        return path
    
    name = rel_parts[-1]
    
    rel_parts = rel_parts[:-1]

    cur_path = root_path

    for part in rel_parts:
        next_dir = pathlib.Path(cur_path) / part
        config = get_config_file(str(next_dir))
        
        if not config:
            cur_path = str(next_dir)
            continue
        
        ctx = {'path': str(next_dir)}

        access_result = config.evaluate_hook('access', ctx)
        if access_result is not None:
            if 'value' in access_result:
                if access_result['value'] is False:
                    raise fuse.FuseOSError(errno.EACCES)

        getattr_result = config.evaluate_hook('getattr', ctx)
        if getattr_result is not None:
            if 'value' in getattr_result:
                if getattr_result['value'] is None:
                    raise fuse.FuseOSError(errno.ENOENT)
                
        if config.directory_map is not None and config.directory_map.condition.evaluate(ctx):
            mapped_path = map_to_path(str(next_dir), config.directory_map.map_to, root_path)
            cur_path = mapped_path
        else:
            cur_path = str(next_dir)
    
    full_path = str(pathlib.Path(cur_path) / name)

    return full_path

def evaluate(config_file: FileConfig, hook: str, ctx: dict, result_callbacks: dict[str, Callable[[Any], None]]) -> bool:
    if config_file:
        result = config_file.evaluate_hook(hook, ctx)
        if result is None:
            return False
        
        valid_callback = False
        
        for key in result_callbacks.keys():
            if key in result:
                result_callbacks[key](result[key])
                valid_callback = True
        return valid_callback
    
    return False
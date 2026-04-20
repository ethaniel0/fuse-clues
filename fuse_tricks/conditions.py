from dataclasses import dataclass
from abc import ABC, abstractmethod
import os
from typing import Literal
import re
import pathlib

#### GENERAL CONDITIONS ####
@dataclass
class Condition(ABC):
    @abstractmethod
    def evaluate(self, ctx: dict) -> bool:
        pass

@dataclass
class AlwaysCondition(Condition):
    def evaluate(self, ctx: dict):
        return True

@dataclass
class AllCondition(Condition):
    conditions: list[Condition]

    def evaluate(self, ctx: dict):
        return all([condition.evaluate(ctx) for condition in self.conditions])

@dataclass
class AnyCondition(Condition):
    conditions: list[Condition]

    def evaluate(self, ctx: dict):
        return any(condition.evaluate(ctx) for condition in self.conditions)
    
@dataclass
class NotCondition(Condition):
    condition: Condition

    def evaluate(self, ctx: dict):
        return not self.condition.evaluate(ctx)

def _detect_root(path, ctx: dict):
    if path.startswith('/'):
        rootpath = ctx['rootpath']
        path = os.path.join(rootpath, path.lstrip('/'))
    return path

@dataclass
class FileExistsCondition(Condition):
    path: str = ""

    def evaluate(self, ctx: dict):
        path = _detect_root(self.path, ctx)
        p = pathlib.Path(ctx['path']).parent
        filepath = str(p / path)
        return os.path.isfile(filepath)
    
@dataclass
class DirExistsCondition(Condition):
    path: str = ""

    def evaluate(self, ctx: dict):
        path = _detect_root(self.path, ctx)
        p = pathlib.Path(ctx['path']).parent
        dirpath = str(p / path)
        return os.path.isdir(dirpath)

def get_file_name(path, ctx: dict):
    name = pathlib.Path(path).name # changed from path to pathlib.Path(path).name
    if path == '': # Special case: check permissions of the current path
        name = pathlib.Path(ctx['path']).name

    p = pathlib.Path(ctx['path']).parent
    
    if path.endswith('\*'):
        name = path[:-2] + '*'
    elif path.endswith('*'):
        relpath = pathlib.Path(path)
        parent = relpath.parent
        if parent.is_absolute():
            parent = parent.relative_to(parent.anchor)
        if parent != pathlib.Path('.'):
            p = p / parent
            
        files = sorted(os.listdir(p))
        files = [f for f in files if not f.endswith('_config.yaml') and not f.startswith('._')]
        if len(files) != 1:
            return None
        name = files[0]

    pathparent = pathlib.Path(path).parent

    return pathparent / name if pathparent != pathlib.Path('.') else name

def _get_file_content(path, ctx: dict):
    p = pathlib.Path(ctx['path']).parent
    name = get_file_name(path, ctx)
    if name is None:
        return None
    
    
    filepath = str(p / name)
    if not os.path.isfile(filepath):
        print(f"File {filepath} does not exist.")
        return None
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            return content
    except Exception as e:
        print(f"Error reading file {filepath}: {e}")
        return None

@dataclass
class FileContentMatchesCondition(Condition):
    path: str
    expected_content: str

    def evaluate(self, ctx: dict):
        path = _detect_root(self.path, ctx)
        content = _get_file_content(path, ctx)
        if content is None:
            print(f"File {self.path} does not exist or could not be read.")
            return False
        match = re.match(self.expected_content, content)
        return bool(match)
        
@dataclass
class FileContentContainsCondition(Condition):
    path: str
    expected_content: str

    def evaluate(self, ctx: dict):
        path = _detect_root(self.path, ctx)
        file_content = _get_file_content(path, ctx)
        if file_content is None:
            print(f"File {self.path,} does not exist or could not be read.")
            return False
        match = re.search(self.expected_content, file_content)
        return bool(match)

@dataclass
class NodeAttributeEqualsCondition(Condition):
    attribute: str
    value: str

    def evaluate(self, ctx: dict):
        return 'state' in ctx and \
            self.attribute in ctx['state'] and \
            ctx['state'][self.attribute] == self.value
    
@dataclass
class PermissionCondition(Condition):
    path: str
    required_perms: str  # bitmask of required permissions

    def evaluate(self, ctx: dict):
        path = _detect_root(self.path, ctx)
        name = get_file_name(path, ctx)
        if name is None:
            return False
        p = pathlib.Path(ctx['path']).parent
        filepath = str(p / name)

        if not os.path.isfile(filepath):
            return False

        # Convert permissions string (e.g. "rw-r--r--") to a bitmask
        perm_bits = 0
        if len(self.required_perms) != 9:
            raise ValueError(f"Invalid permissions string: {self.required_perms}")
        for i, char in enumerate(self.required_perms):
            if char == 'r':
                perm_bits |= (0o400 >> (i // 3) * 3)
            elif char == 'w':
                perm_bits |= (0o200 >> (i // 3) * 3)
            elif char == 'x':
                perm_bits |= (0o100 >> (i // 3) * 3)
            elif char != '-':
                raise ValueError(f"Invalid character in permissions string: {char}")
        try:
            actual_perms = os.stat(filepath).st_mode & 0o777
            return (actual_perms & perm_bits) == perm_bits
        except Exception as e:
            print(f"Error checking permissions for {filepath}: {e}")
            return False

@dataclass
class PermissionRelativeToUserCondition(Condition):
    path: str
    can_read: Literal['user', 'group', 'other', 'no', 'yes']

    def evaluate(self, ctx: dict):
        path = _detect_root(self.path, ctx)
        name = path
        if path == '': # Special case: check permissions of the current path
            name = pathlib.Path(ctx['path']).name

        
        p = pathlib.Path(ctx['path']).parent
        filepath = str(p / name)
        if not os.path.isfile(filepath):
            return False
        
        file_perms = os.stat(filepath).st_mode & 0o777
        
        uid = ctx['uid']
        gid = ctx['gid']
        pid = ctx['pid']
        if self.can_read == 'user':
            return (file_perms & 0o400) and os.stat(filepath).st_uid == uid
        elif self.can_read == 'group':
            return (file_perms & 0o040) and os.stat(filepath).st_gid == gid
        elif self.can_read == 'other':
            return (file_perms & 0o004) != 0
        elif self.can_read == 'yes': # check if the user can read it in any capacity (user, group, or other)
            return (file_perms & 0o400) and os.stat(filepath).st_uid == uid or \
                   (file_perms & 0o040) and os.stat(filepath).st_gid == gid or \
                   (file_perms & 0o004) != 0
        elif self.can_read == 'no':
            return not ((file_perms & 0o400) and os.stat(filepath).st_uid == uid or \
                   (file_perms & 0o040) and os.stat(filepath).st_gid == gid or \
                   (file_perms & 0o004) != 0)
        else:
            raise ValueError(f"Invalid can_read value: {self.can_read}")
    
#### SPECIFIC CONDITIONS ####

@dataclass
class OffsetCondition(Condition):
    offset: int
    mode: str  # 'gte', 'lte', 'gt', 'lt', 'eq'

    def evaluate(self, ctx: dict):
        if 'offset' not in ctx:
            return False
        actual_offset = ctx['offset']
        if self.mode == 'gte':
            if actual_offset >= self.offset:
                ctx['offset'] -= self.offset
                return True
        elif self.mode == 'lte':
            if actual_offset <= self.offset:
                ctx['offset'] -= self.offset
                return True
        elif self.mode == 'gt':
            if actual_offset > self.offset:
                ctx['offset'] -= self.offset
                return True
        elif self.mode == 'lt':
            return actual_offset < self.offset
        elif self.mode == 'eq':
            if actual_offset == self.offset:
                ctx['offset'] -= self.offset
                return True
        else:
            raise ValueError(f"Invalid mode: {self.mode}")
        return False
        
@dataclass
class SizeCondition(Condition):
    size: int
    mode: str  # 'gte', 'lte', 'gt', 'lt', 'eq'

    def evaluate(self, ctx: dict):
        if 'size' not in ctx:
            return False
        actual_size = ctx['size']
        if self.mode == 'gte':
            return actual_size >= self.size
        elif self.mode == 'lte':
            return actual_size <= self.size
        elif self.mode == 'gt':
            return actual_size > self.size
        elif self.mode == 'lt':
            return actual_size < self.size
        elif self.mode == 'eq':
            return actual_size == self.size
        else:
            raise ValueError(f"Invalid mode: {self.mode}")

@dataclass
class FileSizeCondition(Condition):
    path: str
    size: int
    mode: str  # 'gte', 'lte', 'gt', 'lt', 'eq'

    def evaluate(self, ctx: dict):
        path = _detect_root(self.path, ctx)
        name = get_file_name(path, ctx)
        if name is None:
            return False

        p = pathlib.Path(ctx['path']).parent
        filepath = str(p / name)

        if not os.path.isfile(filepath):
            return False

        try:
            actual_size = os.path.getsize(filepath)
        except Exception as e:
            print(f"Error getting size for {filepath}: {e}")
            return False

        if self.mode == 'gte':
            return actual_size >= self.size
        elif self.mode == 'lte':
            return actual_size <= self.size
        elif self.mode == 'gt':
            return actual_size > self.size
        elif self.mode == 'lt':
            return actual_size < self.size
        elif self.mode == 'eq':
            return actual_size == self.size
        else:
            raise ValueError(f"Invalid mode: {self.mode}")
#!/usr/bin/env python

import argparse
import errno
import logging
import os
import pathlib
import stat
import threading
import time
from typing import Any, Optional

import mfusepy as fuse

from engine import config_tools as ct

def with_root_path(func):
    def wrapper(self, path, *args, **kwargs):
        if path is not None:
            if path.endswith('_config.yaml'):
                raise fuse.FuseOSError(errno.ENOENT)  # hide config files
            path = self.root + path
            path = ct.get_real_path(str(path), self.root)
        return func(self, path, *args, **kwargs)

    return wrapper

def static_with_root_path(func):
    def wrapper(self, path, *args, **kwargs):
        if path is not None:
            path = self.root + path
            path = ct.get_real_path(str(path), self.root)
        return func(path, *args, **kwargs)

    return wrapper

def raise_error(error_str: str):
    if error_str == 'no_exist':
        raise fuse.FuseOSError(errno.ENOENT)
    elif error_str == 'access_denied':
        raise fuse.FuseOSError(errno.EACCES)
    


class Loopback(fuse.Operations):
    use_ns = True

    def __init__(self, root):
        self.root = os.path.realpath(root)
        self.rwlock = threading.Lock()
        root_config_name = pathlib.Path(root) / '*'
        print('name: ', str(root_config_name.absolute()))
        self.global_config = ct.get_config_file(str(root_config_name.absolute()))
        print(f"Global config: {self.global_config}")

    def ctx(self, path, **kwargs):
        # get user number and group number of the caller
        uid, gid, pid = fuse.fuse_get_context()
        context = {'path': path, 'uid': uid, 'gid': gid, 'pid': pid, 'rootpath': self.root}
        context.update(kwargs)
        return context

    ############## COMPLETED FUSE METHODS ##############

    @with_root_path
    @fuse.overrides(fuse.Operations)
    def read(self, path: str, size: int, offset: int, fh: int) -> bytes:
        config = ct.get_config_file(path)

        def use_result(result):
            if result is not None:
                if 'error' in result and result['error'] is not None:
                    raise_error(result['error'])
                if 'value' in result:
                    val = result['value'] or ''
                    return True, val.encode() if isinstance(val, str) else val
                if 'map_to' in result:
                    return False, ct.get_real_path(ct.map_to_path(path, result['map_to'], self.root), self.root)
            return False, None

        with self.rwlock:

            context = self.ctx(path, offset=offset, size=size)

            if self.global_config and (result := self.global_config.evaluate_hook('read', context)) is not None:
                ret, val = use_result(result)
                if ret:
                    return val
                elif val is not None:
                    path = val

            elif config and (result := config.evaluate_hook('read', context)) is not None:
                ret, val = use_result(result)
                if ret:
                    return val
                elif val is not None:
                    path = val
            
            with open(path, 'rb') as f:
                f.seek(offset)
                return f.read(size)
        
    @with_root_path
    @fuse.overrides(fuse.Operations)
    def access(self, path: str, amode: int) -> int:
        config = ct.get_config_file(path)

        def use_result(result):
            if result is not None:
                if 'error' in result and result['error'] is not None:
                    raise_error(result['error'])
                if 'map_to' in result:
                    return False, ct.get_real_path(ct.map_to_path(path, result['map_to'], self.root), self.root)
            return False, None
        
        context = self.ctx(path, amode=amode)
        
        if self.global_config and (result := self.global_config.evaluate_hook('access', context)) is not None:
            ret, val = use_result(result)
            if ret:
                return val
            elif val is not None:
                path = val
        elif config and (result := config.evaluate_hook('access', context)) is not None:
            ret, val = use_result(result)
            if ret:
                return val
            elif val is not None:
                path = val
                
        # TODO: check if the user can access, not FUSE itself
        if not os.access(path, amode):
            raise fuse.FuseOSError(errno.EACCES)
        return 0
    
    @with_root_path
    @fuse.overrides(fuse.Operations)
    def readdir(self, path: str, fh: int) -> fuse.ReadDirResult:
        items = ['.', '..']

        def use_search_result(result):
            if result is not None:
                if 'error' in result and result['error'] is not None:
                    raise_error(result['error'])
                if 'value' in result:
                    if result['value'] is None or len(result['value']) == 0:
                        return True, items
                    return True, items + result['value']
                if 'map_to' in result:
                    return False, ct.get_real_path(ct.map_to_path(path, result['map_to'], self.root), self.root)
            return False, None
        def use_listing_result(result):
            if result is not None:
                if 'error' in result and result['error'] is not None:
                    raise_error(result['error'])
                if 'value' in result:
                    if result['value'] is None or len(result['value']) == 0:
                        return True, None
                    return True, result['value']
            return False, None

        dir_context = self.ctx(path)
        dir_config = ct.get_config_file(path)
        if self.global_config and (result := self.global_config.evaluate_hook('readdir_search', dir_context)) is not None:
            ret, val = use_search_result(result)
            if ret:
                return val
            elif val is not None:
                path = val
        elif dir_config and (result := dir_config.evaluate_hook('readdir_search', dir_context)) is not None:
            ret, val = use_search_result(result)
            if ret:
                return val
            elif val is not None:
                path = val

        for item in os.listdir(path):
            if item.endswith('_config.yaml'):
                continue
            full_item_path = os.path.join(path, item)
            config = ct.get_config_file(full_item_path)
            conf_context = self.ctx(full_item_path)

            if self.global_config and (result := self.global_config.evaluate_hook('readdir', conf_context)) is not None:
                cont, val = use_listing_result(result)
                print(f"Global config readdir result for {full_item_path}: {result}, cont: {cont}, val: {val}")
                if cont:
                    items.append(val)
                    continue
            elif config and (result := config.evaluate_hook('readdir', conf_context)) is not None:
                cont, val = use_listing_result(result)
                if cont:
                    if val is not None:
                        items.append(val)
                    continue
                             
            items.append(item)
        return items

    @with_root_path
    @fuse.overrides(fuse.Operations)
    def getattr(self, path: str, fh: Optional[int] = None) -> dict[str, Any]:

        def use_result(result, path):
            if result is None:
                return {}, path
            edits = {}
            if 'error' in result and result['error'] is not None:
                raise_error(result['error'])
            if 'value' in result:
                if result['value'] is None:
                    raise fuse.FuseOSError(errno.ENOENT)
                value = result['value']
                if 'atime' in value:
                    edits['st_atime_ns'] = int(value['atime'] * 1e9)
                if 'mtime' in value:
                    edits['st_mtime_ns'] = int(value['mtime'] * 1e9)
                if 'ctime' in value:
                    edits['st_ctime_ns'] = int(value['ctime'] * 1e9)
                if 'size' in value:
                    edits['st_size'] = value['size']
                if 'mode' in value:
                    edits['st_mode'] = value['mode']
                if 'uid' in value:
                    edits['st_uid'] = value['uid']
                if 'gid' in value:
                    edits['st_gid'] = value['gid']
            if 'map_to' in result:
                path = ct.get_real_path(ct.map_to_path(path, result['map_to'], self.root), self.root)
            return edits, path

        config = ct.get_config_file(path)
        config_edit = {}
        context = self.ctx(path)
        config_exists = True
        if self.global_config and (result := self.global_config.evaluate_hook('getattr', context)) is not None:
            edits, new_path = use_result(result, path)
            config_edit.update(edits)
            path = new_path
            # print('getattr after global config:', path, config_edit)
        elif config and (result := config.evaluate_hook('getattr', context)) is not None:
            edits, new_path = use_result(result, path)
            config_edit.update(edits)
            path = new_path
        else:
            config_exists = False
                
        if fh is not None:
            st = os.fstat(fh)
        elif path is not None:
            
            if config_exists:
                try:
                    st = os.lstat(path)
                except FileNotFoundError:
                    # if the config file exists but the actual file doesn't, return an empty stat result that can be edited by the config file
                    st = os.stat_result(( stat.S_IFREG | 0o644, 0, 0, 0, 0, 0, 0, 0, 0, 0))

            else:
                st = os.lstat(path)

        else:
            raise fuse.FuseOSError(errno.ENOENT)
        
        st_values = {
            'st_atime_ns': st.st_atime_ns or 0,
            'st_ctime_ns': st.st_ctime_ns or 0,
            'st_gid': st.st_gid,
            'st_mode': st.st_mode,
            'st_mtime_ns': st.st_mtime_ns or 0,
            'st_nlink': st.st_nlink,
            'st_size': st.st_size,
            'st_uid': st.st_uid,
        }

        # apply config edits to st
        for key, value in config_edit.items():
            st_values[key] = value

        # print('getattr result:', path, st_values)
        
        return {
            key.removesuffix('_ns'): st_values[key]
            for key in (
                'st_atime_ns',
                'st_ctime_ns',
                'st_gid',
                'st_mode',
                'st_mtime_ns',
                'st_nlink',
                'st_size',
                'st_uid',
            )
        }

    ############## NOT FULLY IMPLEMENTED FUSE METHODS ##############
    
    # TODO: customize offset of write using config file        
    @with_root_path
    @fuse.overrides(fuse.Operations)
    def write(self, path: str, data, offset: int, fh: int) -> int:

        def use_result(result):
            if result is None:
                return False, None
            if 'error' in result and result['error'] is not None:
                raise_error(result['error'])
            if 'value' in result:
                val = result['value']
                if isinstance(val, str):
                    val = val.encode()
                # replace whole file contents with the generated value
                fd = os.open(path, os.O_WRONLY)
                try:
                    os.ftruncate(fd, 0)
                    os.lseek(fd, 0, 0)
                    os.write(fd, val)
                finally:
                    os.close(fd)
                return True, len(data)
            if 'map_to' in result:
                return False, ct.get_real_path(ct.map_to_path(path, result['map_to'], self.root), self.root)
            return False, None
        
        config = ct.get_config_file(path)
        context = self.ctx(path, offset=offset, data=data)
        with self.rwlock:
            if self.global_config and (result := self.global_config.evaluate_hook('write', context)) is not None:
                ret, val = use_result(result)
                if ret:
                    return val
                elif val is not None:
                    path = val
            elif config and (result := config.evaluate_hook('write', context)) is not None:
                ret, val = use_result(result)
                if ret:
                    return val
                elif val is not None:
                    path = val

            fh = os.open(path, os.O_WRONLY)

            os.lseek(fh, offset, 0)
            w = os.write(fh, data)
            os.close(fh)
            return w
    
    @with_root_path
    @fuse.overrides(fuse.Operations)
    def truncate(self, path: str, length: int, fh: Optional[int] = None) -> int:

        def use_result(result):
            if result is None:
                return False, None
            if 'error' in result and result['error'] is not None:
                raise_error(result['error'])
            if 'map_to' in result:
                return False, ct.get_real_path(ct.map_to_path(path, result['map_to'], self.root), self.root)
            return False, None

        config = ct.get_config_file(path)
        context = self.ctx(path, length=length)
        if self.global_config and (result := self.global_config.evaluate_hook('truncate', context)) is not None:
            ret, val = use_result(result)
            if ret:
                return val
            elif val is not None:
                path = val
        elif config and (result := config.evaluate_hook('truncate', context)) is not None:
            ret, val = use_result(result)
            if ret:
                return val
            elif val is not None:
                path = val

        with open(path, 'rb+') as f:
            f.truncate(length)
        return 0

    @with_root_path
    @fuse.overrides(fuse.Operations)
    def rename(self, old: str, new: str):
        if new is not None:
            new = self.root + new
            new = ct.get_real_path(str(new), self.root)  

        def is_vim_backup(path):
            print(path)
            return path.endswith("~") or os.path.basename(path).startswith(".")

        def use_result(result):
            val_old, val_new = old, new
            if result is None or is_vim_backup(new):
                return val_old, val_new
            
            if 'error' in result and result['error'] is not None:
                raise_error(result['error'])
            if 'value' in result:
                value = result['value'] or ''
                if isinstance(value, str):
                    val_new = value
            if 'map_to' in result:
                val_old = ct.get_real_path(ct.map_to_path(old, result['map_to'], self.root), self.root)
            return val_old, val_new

        config = ct.get_config_file(old)
        context = self.ctx(old, new_path=new)
        if self.global_config and (result := self.global_config.evaluate_hook('rename', context)) is not None:
            old, new = use_result(result)
        elif config and (result := config.evaluate_hook('rename', context)) is not None:
            old, new = use_result(result)

        config = ct.get_config_file(old)
        conf_new = ct.get_config_file(new)

        # TODO: with this system, you can unlink a file with its config file by renaming it to something for a different config file. 
        # Then you'd also be able to link an unrelated file to a config file. We should solve this
        if config and not conf_new:
            if is_vim_backup(new):
                return os.rename(old, new)  # skip config rename
            # rename config file
            config_path = ct.get_config_path(old)
            new_config_path = new + "_config.yaml"
            if config_path and os.path.isfile(config_path):
                print(f"Renaming config file {config_path} to {new_config_path}")
                os.rename(config_path, new_config_path)
        return os.rename(old, new)
    
    @with_root_path
    @fuse.overrides(fuse.Operations)
    def unlink(self, path):
        config = ct.get_config_file(path)
        context = self.ctx(path)
        if self.global_config and (result := self.global_config.evaluate_hook('unlink', context)) is not None:
            if 'error' in result and result['error'] is not None:
                raise_error(result['error'])
            if 'map_to' in result:
                path = ct.get_real_path(ct.map_to_path(path, result['map_to'], self.root), self.root)
        elif config and (result := config.evaluate_hook('unlink', context)) is not None:
            if 'error' in result and result['error'] is not None:
                raise_error(result['error'])
            if 'map_to' in result:
                path = ct.get_real_path(ct.map_to_path(path, result['map_to'], self.root), self.root)
        return os.unlink(path)
    
    @with_root_path
    @fuse.overrides(fuse.Operations)
    def rmdir(self, path):
        config = ct.get_config_file(path)
        context = self.ctx(path)
        if self.global_config and (result := self.global_config.evaluate_hook('rmdir', context)) is not None:
            if 'error' in result and result['error'] is not None:
                raise_error(result['error'])
            if 'map_to' in result:
                path = ct.get_real_path(ct.map_to_path(path, result['map_to'], self.root), self.root)
        elif config and (result := config.evaluate_hook('rmdir', context)) is not None:
            if 'error' in result and result['error'] is not None:
                raise_error(result['error'])
            if 'map_to' in result:
                path = ct.get_real_path(ct.map_to_path(path, result['map_to'], self.root), self.root)
        return os.rmdir(path)
    
    ############## UNIMPLEMENTED FUSE METHODS ##############

    chmod = static_with_root_path(os.chmod)
    chown = static_with_root_path(os.chown)

    @with_root_path
    @fuse.overrides(fuse.Operations)
    def create(self, path: str, mode: int, fi=None) -> int:
        return os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)

    @with_root_path
    @fuse.overrides(fuse.Operations)
    def flush(self, path: str, fh: int) -> int:
        os.fsync(fh)
        return 0

    @with_root_path
    @fuse.overrides(fuse.Operations)
    def fsync(self, path: str, datasync: int, fh: int) -> int:
        try:
            if datasync != 0 and hasattr(os, "fdatasync"):
                os.fdatasync(fh)
            else:
                os.fsync(fh)
        except AttributeError:
            os.fsync(fh)
        return 0


    @with_root_path
    @fuse.overrides(fuse.Operations)
    def link(self, target: str, source: str):
        return os.link(self.root + source, target)

    mkdir = static_with_root_path(os.mkdir)
    open = static_with_root_path(os.open)

    @with_root_path
    @fuse.overrides(fuse.Operations)
    def mknod(self, path: str, mode: int, dev: int):
        # OpenBSD calls mknod + open instead of create.
        if stat.S_ISREG(mode):
            # OpenBSD does not allow using os.mknod to create regular files.
            fd = os.open(path, os.O_CREAT | os.O_WRONLY | os.O_EXCL, mode & 0o7777)
            os.close(fd)
        else:
            os.mknod(path, mode, dev)
        return 0

    readlink = static_with_root_path(os.readlink)

    @with_root_path
    @fuse.overrides(fuse.Operations)
    def release(self, path: str, fh: int) -> int:
        os.close(fh)
        return 0


    @with_root_path
    @fuse.overrides(fuse.Operations)
    def statfs(self, path: str) -> dict[str, int]:
        stv = os.statvfs(path)
        return {
            key: getattr(stv, key)
            for key in (
                'f_bavail',
                'f_bfree',
                'f_blocks',
                'f_bsize',
                'f_favail',
                'f_ffree',
                'f_files',
                'f_flag',
                'f_frsize',
                'f_namemax',
            )
        }

    @with_root_path
    @fuse.overrides(fuse.Operations)
    def symlink(self, target: str, source: str):
        return os.symlink(source, target)
    
    

    @with_root_path
    @fuse.overrides(fuse.Operations)
    def utimens(self, path: str, times: Optional[tuple[int, int]] = None) -> int:
        now = int(time.time() * 1e9)
        os.utime(path, ns=times or (now, now))
        return 0

def cli(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('root')
    parser.add_argument('mount')
    args = parser.parse_args(args)

    logging.basicConfig(level=logging.DEBUG)
    fuse.FUSE(Loopback(args.root), args.mount, foreground=True, direct_io=True)


if __name__ == '__main__':
    cli()
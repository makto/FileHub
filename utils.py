#-*- coding: utf-8 -*-

import os.path
import hashlib


byte_map = ('B', 'KB', 'MB', 'GB', 'TB')

def size_readify(size, precise=1):
    """do this kind of things:
    1024 => 1 KB"""
    level = 0
    while size >= 1024:
        size = size / 1024.0
        level += 1
    return str(round(size, precise)) + ' ' + byte_map[level]

def make_relpath(self, name, path):
    """返回唯一的相对路径"""
    relpath = os.path.join(path, name)
    while self.db.get_file(relpath) != None:
        name = 'new-' + name
        relpath = os.path.join(path, name)
    return relpath

def md5(content):
    tmp = hashlib.md5()
    tmp.update(content)
    return tmp.hexdigest()

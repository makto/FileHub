#-*- coding: utf-8 -*-
"""
所有有关数据库的操作，都封装为SQLiteDB类下的方法

# 约定
  - 文件名、文件夹结构在数据库与磁盘中保持一致
  - 不通过结尾的/来区分目录和文件，统一作去/处理

# Todo
  - 检查文件是否已上传过（md5?）
  - 磁盘空间限制的显示

"""

import sqlite3

from utils import size_readify

# 表结构
# file表实际上是dir字段到relpath字段的映射表
#       其他字段是说明性的，包括主键id
#       relpath即可标识唯一的一行
init_script = """
    begin;
    create table user (
        id integer not null primary key,
        nickname text not null unique,
        password text not null,
        super integer not null default 0,
        date timestamp not null default (datetime('now', 'localtime'))
    );
    create table file (
        id integer not null primary key,
        name text not null,
        type text not null,
        dir text not null,
        relpath text not null unique,
        owner integer not null,
        ownername text not null,
        size integer not null default 0,
        size_readable text not null default '0B',
        hash text,
        date timestamp not null default (datetime('now', 'localtime')),
        foreign key(owner) references user(id)
    );
    create index file_1 on file(dir);
    insert into user (id, nickname, password) values (1, 'nobody', '');
    insert into user (id, nickname, password, super) values (2, 'makto', 'toruk', 1);
    commit;
"""


class SQLiteDB(object):
    def __init__(self, dbname):
        self.conn = sqlite3.connect(dbname)
        try:
            self.conn.execute('select * from file where 1=0')
        except sqlite3.OperationalError:
            self.conn.executescript(init_script)
            self.conn.commit()
        self.conn.row_factory = sqlite3.Row

    def get_user_by_id(self, uid):
        c = self.conn.cursor()
        sql = 'select id, nickname, super from user where id=?'
        c.execute(sql, (uid,))
        user = c.fetchone()
        c.close()
        return user

    def get_user(self, uname):
        c = self.conn.cursor()
        sql = 'select * from user where nickname=?'
        c.execute(sql, (uname,))
        user = c.fetchone()
        c.close()
        return user

    def create_user(self, uname, upass):
        c = self.conn.cursor()
        sql = 'insert into user (nickname, password) values (?, ?)'
        c.execute(sql, (uname, upass))
        self.conn.commit()
        c.close()
        return self.get_user(uname)

    def get_files(self, path):
        """返回path下的所有文件
        以创建时间顺序排列
        目录和文件作为两个列表返回"""
        if path != '/':
            path = path.rstrip('/')
        c = self.conn.cursor()
        sql = 'select name, type, owner, ownername, size_readable, ' +\
              'relpath, date, id ' +\
              'from file where dir=? order by date'
        params = (path,)
        c.execute(sql, params)
        allfiles = c.fetchall()
        c.close()
        dirs = []
        files = []
        for f in allfiles:
            if f['type'] == 'dir':
                dirs.append(f)
            else:
                files.append(f)
        return dirs, files

    def save_file(self, fileinfo):
        c = self.conn.cursor()
        sql = 'insert into file ' +\
          '(name, type, dir, relpath, owner, size, ' +\
          'size_readable, hash, ownername) ' +\
          'values (:name, :type, :dir, :relpath, ' +\
          ':owner, :size, :size_readable, :hash, :ownername)'
        if fileinfo['type'] == 'dir':
            fileinfo['size'] = 0
            fileinfo['hash'] = ''
        fileinfo['size_readable'] = size_readify(int(fileinfo['size']))
        c.execute(sql, fileinfo)
        self.conn.commit()
        c.close()

    def get_file(self, relpath='', fid=''):
        """获取由relpath或fid唯一标识的file"""
        pvalue = relpath if relpath else fid
        pname = 'relpath' if relpath else 'id'
        sql = 'select id, type, relpath, owner from file where %s=?'%pname

        c = self.conn.cursor()
        finfo = c.execute(sql, (pvalue,)).fetchone()
        c.close()
        return finfo

    def del_file(self, relpath='', fid=''):
        pvalue = relpath if relpath else fid
        if not pvalue:
            return
        pname = 'relpath' if relpath else 'id'
        sql1 = 'select type from file where %s=?' % pname
        sql2 = 'delete from file where %s=?' % pname
        sql3 = 'delete from file where dir=?' 

        c = self.conn.cursor()
        finfo = c.execute(sql1, (pvalue,)).fetchone()
        if not finfo:
            return
        elif finfo['type'] == 'dir':
            c.execute(sql2, (pvalue,))
            c.execute(sql3, (pvalue,))
        else:
            c.execute(sql2, (pvalue,))
        self.conn.commit()
        c.close()
        return finfo

    def has_dir(self, name):
        """不通过路径后缀/来区分目录和文件
        统一做去后缀的处理"""
        if name == '/':
            return True
        c = self.conn.cursor()
        sql = 'select id from file where type=? and relpath=?'
        params = ('dir', name.rstrip('/'))
        c.execute(sql, params)
        dirs = c.fetchall()
        c.close()
        return bool(dirs)


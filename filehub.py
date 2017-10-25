#! /usr/bin/env python
#-*- coding: utf-8 -*-
"""
FileHub Project based on Tornado

@ makto
@ 2013-05-31
@ BUPT-NRB-818
"""

import os.path
import os
import shutil

import chardet
import tornado.ioloop
import tornado.web
import tornado.options
import tornado.escape
from tornado.web import HTTPError
from tornado.options import options, define
import tornado.gen

import db
import utils
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
cur_dir = os.path.abspath(os.path.dirname(__file__))
define("files_path", default=os.path.join(cur_dir, 'files'))
define("static_server", default='tornado')


class Application(tornado.web.Application):
    def __init__(self):
        assert os.path.isdir(options.files_path),\
               '用于保存文件的目录不存在: %s'%options.files_path
        handlers = [
            (r'/', Index),
            (r'/user/?', User),
            (r'/files/?', Files),
            (r'/handle/?', Handle),
        ]
        if options.static_server == 'tornado':
            handlers.append((r'/files/(.*)', StaticFileHandler,
                            {'path':options.files_path}))
        settings = dict(
            debug = True,
            gzip = True,
            cookie_secret = 'winter is coming',
            template_path = os.path.join(cur_dir, 'templates'),
            static_path = os.path.join(cur_dir, 'static'),
        )
        super(Application, self).__init__(handlers, **settings)
        if os.path.exists(os.path.join(cur_dir, 'data.db')):
            isFirst=False
        else:
            isFirst=True
        self.db = db.SQLiteDB(os.path.join(cur_dir, 'data.db'))
        # os.chdir(options.files_path)
        if isFirst:
            for fpathe,dirs,fs in os.walk(options.files_path):
                print fpathe,dirs,fs
                dirspath = os.path.relpath(fpathe).lstrip("files")
                if dirspath == '':
                    dirspath = '/'
                dirspath=dirspath.replace('\\', '/')
                finfo = dict(dir=dirspath, owner=2, ownername='nao')
                # 文件夹类型
                for dir in dirs:

                    relpath = os.path.join(dirspath,dir)
                    relpath = relpath.replace('\\', '/')

                    finfo.update({'name': dir,
                              'type': 'dir', 'relpath': relpath})
                    self.db.save_file(finfo)
                # 文件
                for file in fs:
                    fullpath = os.path.join(fpathe,file)
                    # print fullpath
                    relpath = os.path.join(dirspath,file)
                    # print relpath
                    relpath = relpath.replace('\\', '/')
                    # print chardet.detect(file)
                    # print type(file)
                    # filePath = file.decode("iso-8859-1")
                    # print filePath
                    size = os.path.getsize(fullpath)
                    # print size
                    finfo.update({'name': relpath   , 'type': 'local',
                                  'relpath': relpath, 'size': size,
                                  'hash': ''})
                    self.db.save_file(finfo)


        else:
            print 'not first'


class BaseHandler(tornado.web.RequestHandler):
    @property
    def db(self):
        return self.application.db
 
    def get_current_user(self):
        # default is user 'nobody'
        user_json = self.get_secure_cookie('user')
        if user_json:
            return tornado.escape.json_decode(user_json)
        else:
            return self.db.get_user_by_id(1)


class StaticFileHandler(tornado.web.StaticFileHandler):
    def set_extra_headers(self, path):
        self.set_header('Content-Disposition', 'attachment')


class Index(BaseHandler):
    def get(self):
        server = options.static_server
        if server == 'nginx':
            upload_url = '/upload/'
        elif server == 'tornado':
            upload_url = '/files/'
        else:
            pass # what else?

        uname = self.current_user['nickname']
        self.render('index.html',upload_url=upload_url,
                                 uname=uname)


class User(BaseHandler):
    def post(self):
        """登陆或注册"""
        uname = self.get_argument('uname')
        upass = self.get_argument('upass')
        user = self.db.get_user(uname)
        if user:
            if user['password'] != upass:
                self.write('密码错误')
                return
        else:
            user = self.db.create_user(uname, upass)
        self.set_secure_cookie('user',
                        tornado.escape.json_encode(dict(user)))
        self.write('ok')

    def delete(self):
        """退出登陆"""
        self.clear_cookie('user')
        self.write('ok')


class Files(BaseHandler):
    """将文件/目录看作同一种资源"""

    def get(self):
        """返回path目录下的所有文件列表"""
        path = self.get_argument('path')
        dirs, files = self.db.get_files(path)

        server = options.static_server
        if server == 'nginx':
            dl_prefix = '/download'
        elif server == 'tornado':
            dl_prefix = '/files'
        else:
            pass # what else?
        self.render('files.html', files=files, dirs=dirs,
                    dl_prefix=dl_prefix)

    @tornado.gen.coroutine
    def post(self):
        """创建文件/目录
        若使用nginx处理upload，则文件的创建会交给Handle"""
        path = self.get_argument('path')
        if not self.db.has_dir(path):
            # not caused by user, just raise it
            raise HTTPError(404, 'target dir not exists')
        owner = self.current_user['id']
        ownername = self.current_user['nickname']
        finfo = dict(dir=path, owner=owner, ownername=ownername)
        filetype = self.get_argument('type')
        assert filetype in ('dir', 'file')
        if filetype == 'file':
            assert options.static_server == 'tornado'
            files = self.request.files.get('file')
            for f in files:
                relpath = utils.make_relpath(self, f.filename, path)
                fullpath = os.path.join(options.files_path,relpath[1:])
                                        # relpath.lstrip('/'))
                with open(fullpath, 'wb') as tmp:
                    yield tmp.write(f.body)
                finfo.update({'name': f.filename, 'type': f.content_type,
                              'relpath': relpath, 'size': len(f.body),
                              'hash': utils.md5(f.body)})
                self.db.save_file(finfo)
        else: # filetype == 'dir'
            relpath = utils.make_relpath(self, self.get_argument('name'), path)
            relpath = relpath.replace('\\', '/')
            fullpath = os.path.join(options.files_path, relpath.lstrip('/'))
            os.mkdir(fullpath)
            finfo.update({'name': self.get_argument('name'),
                          'type': filetype, 'relpath': relpath})
            self.db.save_file(finfo)

        self.write('ok')

    def delete(self):
        """删除文件/目录"""
        owner = self.current_user['id']
        issuper = self.current_user['super']
        fid = self.get_argument("fid")
        finfo = self.db.get_file(fid=fid)
        if not finfo:
            raise HTTPError(404, 'no such file exists')
        # 除以下三种情况，其余情况下都不允许删除
        # 匿名用户创建的文件
        # 该登陆用户创建的文件
        # 该用户为超级用户
        elif finfo['owner'] != 1 and finfo['owner'] != owner and not issuper:
            raise HTTPError(403, 'you have no permission')
        else:
            fullpath = os.path.join(options.files_path,
                                    finfo['relpath'].lstrip('/'))
            try:
                if finfo['type'] == 'dir':
                    shutil.rmtree(fullpath)
                else:
                    os.remove(fullpath)
            except OSError:
                pass
            self.db.del_file(fid=fid)
        self.write('ok')


class Handle(BaseHandler):
    def post(self):
        """由nginx upload module转发过来
        将上传文件复制到指定文件夹下"""
        path = self.get_argument('path')
        if not self.db.has_dir(path):
            raise HTTPError(404, 'target dir not exists')
        name = self.get_argument('file.name')
        relpath = utils.make_relpath(self, name, path)

        src_path = self.get_argument('file.path')
        full_path = os.path.join(options.files_path, relpath.lstrip('/'))
        shutil.copyfile(src_path, full_path)
        finfo = dict(name=name,
                     dir=path,
                     relpath=relpath,
                     type=self.get_argument('file.content_type'),
                     size = self.get_argument('file.size'),
                     hash = self.get_argument('file.md5'),
                     owner = self.current_user['id'],
                     ownername = self.current_user['nickname'])
        self.db.save_file(finfo)
        self.write('ok')


if __name__ == '__main__':
    tornado.options.parse_config_file(os.path.join(cur_dir, 'config.py'))
    app = Application()
    app.listen(8888)
    tornado.ioloop.IOLoop.instance().start()


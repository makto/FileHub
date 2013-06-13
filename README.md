# FileHub

## what's this

file sharing web app

you can upload, download, delete, etc

## how to use it

1. `sudo pip install tornado`
2. `python filehub.py`

then it's up and running on localhost:8888

## customization

### using nginx

by default FileHub handles file upload/download with tornado itself, for fast-setup consideration

but tornado is not so efficient in serving static files and especially uploading files (limited by RAM or so, people say)

so FileHub comes with nginx support

you can easily switch to nginx:

1. install nginx with [nginx upload module](https://github.com/vkholodkov/nginx-upload-module)
2. put `nginx.conf` to `/etc/nginx/site-enabled/` (may differ for different OS)
3. change the following fields in `filehub.conf` on your needs:
  - `root` in `location ^~ /static/`
  - `alias` in `location /download/`
  - `upload_store` in `location /upload/` (make sure you create it)
4. uncomment `static_server = 'nginx'` in `config.py`

that's it

### files location

files will be uploaded to `files/` folder right in FileHub root directory by default

you can change that by modifying `files_path` in `config.py`

this may be useful if you want to store files on another disk

## future features

- display corresponding icons for different type of file
- display uploading progress for individual file
- handle uploading errors

## built with & thanks to

- [Tornado](https://github.com/facebook/tornado)
- [jQuery](https://github.com/jquery/jquery)
- [Pure](https://github.com/yui/pure)
- [jQuery File Uploader](https://github.com/blueimp/jQuery-File-Upload)
- [nginx upload module](https://github.com/vkholodkov/nginx-upload-module)

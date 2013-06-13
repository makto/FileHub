##### files path #####
# where files will be uploaded to
# as well as downloaded to
# default to the folder /files/ in the project root
# uncomment to change
######################
#
# files_path = '/path/to/your/custom/files/dir'


##### static_server #####
# designate the static server: tornado or nginx
# be responsible for things:
#
#    - serving /static/ folder
#
#    - handling file upload
#      - nginx with url pattern /upload/
#      - tornado with url pattern /files/
#
#    - handling file download
#      - nginx with url pattern /download/
#      - tornado with url pattern /files/(*.)
#
# just use the pattern stated above, modifying them makes no sense
# default to tornado for quick setup, uncomment to change
#########################
#
# static_server = 'nginx'


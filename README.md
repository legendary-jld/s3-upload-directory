# s3-upload-directory
A Python3 script to upload all files from a directory to s3, while maintaining directory structure and assigning valid content-types

####Example config file:
**config.yml**
> aws:
> &emsp; aws_access_key_id: '<i>your_key_id</i>'
> &emsp;aws_access_key_secret: '<i>your_key_secret</i>'
> &emsp;default_bucket: '<i>bucket_name</i>'

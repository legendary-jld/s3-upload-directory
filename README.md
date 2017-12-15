# s3-upload-directory
A Python3 script to upload all files from a directory to s3, while maintaining directory structure and assigning valid content-types

####Example config file:
**config.yml**
> aws:<br>
> &emsp; aws_access_key_id: '<i>your_key_id</i>'<br>
> &emsp;aws_access_key_secret: '<i>your_key_secret</i>'<br>
> &emsp;default_bucket: '<i>bucket_name</i>'<br>

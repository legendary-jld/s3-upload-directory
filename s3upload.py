import boto3, botocore
import os.path
import sys
import yaml
import definitions
import time

MAX_SIZE = 20 * 1000 * 1000 # max size in bytes before uploading in parts. between 1 and 5 GB recommended
PART_SIZE = 6 * 1000 * 1000 # size of parts when uploading in parts

FILE_ITERATION = 0
FILE_ITERATION_TOTAL = 0
CURRENT_FILE = ""
CURRENT_FILE_SIZE = 0

def bytes_to_readable(bytes):
    if bytes > 999999:
        return "{:,.2f}mb".format(bytes / 1000 / 1000)
    elif bytes > 999:
        return "{:,}kb".format(bytes / 1000)
    else:
        return "{:,}b".format(bytes / 1000)

def update_progress(progress):
    barLength = 10 # Modify this to change the length of the progress bar
    status = ""
    if isinstance(progress, int):
        progress = float(progress)
    if not isinstance(progress, float):
        progress = 0
        status = "error: progress var must be float\r\n"
    if progress < 0:
        progress = 0
        status = "Halt...\r\n"
    if progress >= 1:
        progress = 1
        status = "Done...\r\n"
    block = int(round(barLength*progress))
    text = "\r== {0}/{1} files: [{2}] {3}% {4} {5}".format(FILE_ITERATION, FILE_ITERATION_TOTAL, "#"*block + "-"*(barLength-block), progress*100, CURRENT_FILE, status)
    sys.stdout.write(text)
    sys.stdout.flush()

def percent_cb(complete):
    total = CURRENT_FILE_SIZE
    percent_complete = float("{:.2f}".format(round(complete/total, 2)))
    update_progress(percent_complete)

def user_input(output_text, is_bool=False):
    response = input("{0} ".format(output_text))

    if response == "exit":
        exit()

    if is_bool:
        if response.lower() in ("y", "yes", "true"):
            return True
        else:
            return False
    return response

with open("config.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile)

print("== botos3upload.py - Mass upload files to s3")
print("== (type 'exit' at any time to quit)")
# Fill these in - you get them when you sign up for S3
AWS_ACCESS_KEY_ID = cfg["aws"]["aws_access_key_id"]
AWS_ACCESS_KEY_SECRET = cfg["aws"]["aws_access_key_secret"]
DEFAULT_BUCKET = cfg["aws"]["default_bucket"]
print("== LOADED - AWS_ACCESS_KEY_ID:", AWS_ACCESS_KEY_ID)
print("== LOADED - AWS_ACCESS_KEY_SECRET:", "{0}***".format(AWS_ACCESS_KEY_SECRET[:4]),)

# conn = boto.connect_s3(AWS_ACCESS_KEY_ID, AWS_ACCESS_KEY_SECRET)
s3 = boto3.resource('s3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_ACCESS_KEY_SECRET)

def bucket_loop():
    exists = False
    while not exists:
        bucket_name = user_input("Please enter the bucket name (empty for default):")
        if len(bucket_name) ==  0:
            bucket_name = DEFAULT_BUCKET
            # print("== Default bucket loaded:", bucket_name)
        bucket = s3.Bucket(bucket_name)
        exists = True
        try:
            s3.meta.client.head_bucket(Bucket=bucket_name)
        except botocore.exceptions.NoCredentialsError as e:
            # Credentials must have been no good
            print("== The credentials you provided were invalid, please reconfigure.")
            exit()
        except botocore.exceptions.ClientError as e:
            # If a client error is thrown, then check that it was a 404 error.
            # If it was a 404 error, then the bucket does not exist.
            error_code = int(e.response['Error']['Code'])
            if error_code == 404:
                exists = False
            print("== Could not access the bucket provided, creating new bucket")
            bucket = s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': 'us-east-1'}
                )
    # print("== Bucket successfully accessed: ", bucket_name)
    return bucket, bucket_name

bucket = None
bucket_name = ""
unconfirmed = True
while unconfirmed:
    bucket, bucket_name = bucket_loop()
    sourceDir = user_input("What directory would you like to upload:") # /home/jboo/Git/richsicecream/static/
    destDir = user_input("Place files in directory inside bucket (optional):")

    print("== Moving files from '{0}' to '{1}' in bucket '{2}'".format(sourceDir, destDir, bucket_name))
    if user_input("Is this correct? (yes/no)", is_bool=True):
        unconfirmed = False

filesInfo = []
fileStats = {
    "count": 0,
    "total_size": 0
}
for directory_path, subdirs, files in os.walk(sourceDir):
    for filename in files:
        full_path = os.path.join(directory_path, filename)
        filesize = os.path.getsize(full_path)
        ext = os.path.splitext(full_path)[1]
        if len(ext) > 0:
            filesInfo.append({
                "filename": filename,
                "full_path": full_path,
                "new_path": "{0}{1}".format(destDir,full_path[len(sourceDir):]),
                "file_size": filesize,
                "ext": ext,
                "content_type": definitions.ContentTypes[ext]
            })
            fileStats["count"] = fileStats["count"] + 1
            fileStats["total_size"] = fileStats["total_size"] + filesize
        else:
            print("== Skipping file:", filename)
print("== Total Files:", fileStats["count"], "(size: {0})".format(bytes_to_readable(fileStats["total_size"])))


s3Client = s3.meta.client
FILE_ITERATION_TOTAL = fileStats["count"]
errors = []
for record in filesInfo:
    FILE_ITERATION = FILE_ITERATION + 1
    CURRENT_FILE = record["filename"]
    CURRENT_FILE_SIZE = record["file_size"]
    ExtraArgs = {
    "ContentType": record['content_type']
    }
    with open(record["full_path"], 'rb') as data:
        # print(record)
        try:
            s3Client.upload_fileobj(data, bucket_name, record["new_path"], ExtraArgs=ExtraArgs, Callback=percent_cb)
        except Exception as e:
            errors.append(e)
            percent_cb(100,100)
print("")
print("== Upload Complete")
if errors:
    print("== Errors:", errors)

    # Fileobj (a file-like object) -- A file-like object to upload. At a minimum, it must implement the read method, and must return bytes.
    # Bucket (str) -- The name of the bucket to upload to.
    # Key (str) -- The name of the key to upload to.
    # ExtraArgs (dict) -- Extra arguments that may be passed to the client operation.
    # Callback (method) -- A method which takes a number of bytes transferred to be periodically called during the upload.
    # Config (boto3.s3.transfer.TransferConfig) -- The transfer configuration to be used when performing the upload.

exit()

import boto3
import os
import random
import string

def randomStringDigits(stringLength=6):
    """Generate a random string of letters and digits """
    lettersAndDigits = string.ascii_letters + string.digits
    return ''.join(random.choice(lettersAndDigits) for i in range(stringLength))

def upload_file_to_s3(input, bucket, bucket_folder, filename):
    """
    Function to upload a file to an S3 bucket
    """
    session = boto3.Session(region_name='us-east-2',
                            aws_access_key_id='AKIA2LZFGPYQFYUICFNH',
                            aws_secret_access_key='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')
    s3 = session.client('s3')
    object = '%s/%s' % (bucket_folder, filename)
    response = s3.upload_file(input, bucket, object, ExtraArgs={'ContentType': "image/jpeg", 'ACL': "public-read"})
    # s3.put_object_acl(ACL='public-read', Bucket=bucket, Key=object)

    return response

def delete_file_in_s3(bucket, object):
    """
    Function to download a given file from an S3 bucket
    """
    session = boto3.Session(region_name='us-east-2',
                            aws_access_key_id='AKIA2LZFGPYQFYUICFNH',
                            aws_secret_access_key='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')
    s3 = session.client('s3')
    response = s3.delete_object(Bucket=bucket, Key=object)

    return response

def download_file_from_s3(output_path, filename, bucket, bucket_folder):
    """
    Function to download a given file from an S3 bucket
    """
    s3 = boto3.resource('s3')
    output = f"{output_path}/{filename}"
    s3.Bucket(bucket).download_file(filename, output)

    return output

def list_files_in_s3(bucket, bucket_folder):
    """
    Function to list files in a given S3 bucket
    """
#    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
#    if not AWS_ACCESS_KEY_ID:
#        raise ValueError("No AWS_ACCESS_KEY_ID set for Flask application")
#
#    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
#    if not AWS_SECRET_ACCESS_KEY:
#        raise ValueError("No AWS_SECRET_ACCESS_KEY set for Flask application")
#
#    session = boto3.Session(region_name='us-east-2',
#                            aws_access_key_id=AWS_ACCESS_KEY_ID,
#                            aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    session = boto3.Session(region_name='us-east-2',
                            aws_access_key_id='AKIA2LZFGPYQFYUICFNH',
                            aws_secret_access_key='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')
    s3 = session.resource('s3')
    my_bucket = s3.Bucket(bucket)
    contents = []
    for item in my_bucket.objects.filter(Prefix=bucket_folder):
        contents.append(item.key)

    return contents


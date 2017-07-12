import os
import base64
import botocore
import boto3
import json
import urllib
from chalice import BadRequestError
from chalice import ChaliceViewError
from chalice import Chalice

app = Chalice(app_name='a3x')
app.debug = True
REGION = 'us-east-1'

BUCKET = 'freko-001'
S3 = boto3.resource('s3')

REKOGNITION = boto3.client('rekognition')

@app.route('/face', methods=['POST'], content_types=['application/json'], api_key_required=True)
def face():
    req = app.current_request.json_body
    # parse request to prepare file
    file_basename, img_data = parse_request(req)
    ## create temp file
    image_file = open_image_file(file_basename, img_data)
    ## create s3 bucket if not exists
    create_s3_bucket_if_not_exists()
    ## upload file to s3 bucket
    upload_file_s3_bucket(file_basename, image_file.name)
    ## delete temp file
    close_image_file(image_file)
    ## detect faces
    # res = detect_faces(file_basename)
    # return {'respone': file_basename}
    res = rec_c(file_basename)
    return search_response(res)


def parse_request(req):
    file_name = must_get_value(req, 'name')
    img_data = decode_base64(must_get_value(req, 'base64'))
    return file_name, img_data

def must_get_value(req, key):
    try:
        return req[key]
    except KeyError:
        raise BadRequestError(key + ' is not found')

def decode_base64(data):
    try:
        missing_padding = len(data) % 4
        if missing_padding != 0:
            data += b'='* (4 - missing_padding)
        return base64.b64decode(data)
    except Exception:
        raise BadRequestError("base64 is not decodable")

def open_image_file(name, data):
    try:
        image_file = open('/tmp/' + name, 'wb+')
        image_file.write(data)
        return image_file
    except Exception as ex:
        raise ChaliceViewError("file is not openable. error = " + ex.message)

def create_s3_bucket_if_not_exists():
    exists = True
    try:
        S3.meta.client.head_bucket(Bucket=BUCKET)
    except botocore.exceptions.ClientError as ex:
        # If a client error is thrown, then check that it was a 404 error.
        # If it was a 404 error, then the bucket does not exist.
        error_code = int(ex.response['Error']['Code'])
        if error_code == 404:
            exists = False
    if exists:
        return
    else:
        try:
            S3.create_bucket(Bucket=BUCKET, CreateBucketConfiguration={
                'LocationConstraint': REGION})
        except Exception as ex:
            raise ChaliceViewError("fail to create bucket s3. error = " + ex.message)
    return

def upload_file_s3_bucket(obj_name, image_file_name):
    try:
        s3_object = S3.Object(BUCKET, obj_name)
        s3_object.upload_file(image_file_name)
    except Exception as ex:
        raise ChaliceViewError("fail to upload file s3. error = " + ex.message)

def close_image_file(image_file):
    try:
        image_file.close()
        os.remove(image_file.name)
    except Exception as ex:
        raise ChaliceViewError("file is not closable. error = " + ex.message)

def rec_c(name):
    # try:
        # return name
    response = REKOGNITION.recognize_celebrities(
        Image={
            'S3Object': {
                'Bucket': BUCKET,
                'Name': name,
            }
        }
    )
    return response
    # except Exception as ex:
    #     raise ChaliceViewError("fail to detect faces. error = " + str(type(ex))) 

def search_response(res):
    # read name of the person in the picture from JSON
    ans = {}
    json_dict = res
    name = json_dict["CelebrityFaces"][0]["Name"]
    ans['Name'] = name
    # search with google custom search API
    api_key = 'AIzaSyB8aEOTYwqX2UT6GE_2a1LDjVc4b_nymI0'
    search_engine_ID = '013044299581177508447:irovpa3a1yo'
    tbm = 'nws'
    url = 'https://www.googleapis.com/customsearch/v1'

    params = {
            'key': api_key,
            'cx': search_engine_ID,
            'tbm': tbm,
            'q': name.encode('utf-8')
            }
    data = urllib.parse.urlencode(params)
    full_url = url + '?' + data
    response = urllib.request.urlopen(full_url)
    result = json.load(response)
    ans['news'] = []
    for item in result['items']:
        ans['news'].append((item['title'], item['link']))
    return ans 

from minio import Minio
import json
import os

config = 'minio_config.json'
with open(config, 'r') as f:
	minio_config = json.load(f)
	endpoint = minio_config['endpoint']
	access_key = minio_config['access_key']
	secret_key = minio_config['secret_key']

client = Minio(endpoint=endpoint, access_key=access_key, secret_key=secret_key, secure=False)
bucket_name = 'openwhisk'
found = client.bucket_exists(bucket_name)
if not found:
	client.make_bucket(bucket_name)
else:
	print(f'Bucket {bucket_name} already exists')

data_dir = '../../dataset'
vid_dir = f'{data_dir}/video'
img_dir = f'{data_dir}/image'

for file in os.listdir(vid_dir):
	path = f'{vid_dir}/{file}'
	client.fput_object(bucket_name=bucket_name, object_name=file, file_path=path)

for file in os.listdir(img_dir):
	path = f'{img_dir}/{file}'
	client.fput_object(bucket_name=bucket_name, object_name=file, file_path=path)

# dataset from https://www.kaggle.com/datasets/ltcmdrdata/plain-text-wikipedia-202011
mapreduce_bucket = 'mapreduce'
mapreduce_dir = '../../dataset/mapreduce/enwiki20201020'

found = client.bucket_exists(mapreduce_bucket)
if not found:
	client.make_bucket(mapreduce_bucket)
else:
	print(f'Bucket {mapreduce_bucket} already exists')

for file in os.listdir(mapreduce_dir):
	path = f'{mapreduce_dir}/{file}'
	client.fput_object(bucket_name=mapreduce_bucket, object_name=file, file_path=path)

# create bucket for mapreduce mappers
job_bucket = 'jobbucket'
found = client.bucket_exists(job_bucket)
if not found:
	client.make_bucket(job_bucket)
else:
	print(f'Bucket {job_bucket} already exists')
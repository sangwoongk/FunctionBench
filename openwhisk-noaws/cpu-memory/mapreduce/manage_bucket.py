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

num_bucket = 10
for i in range(num_bucket):
	name = f'jobbucket{i}'
	client.make_bucket(name)
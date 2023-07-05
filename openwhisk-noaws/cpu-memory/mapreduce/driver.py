from minio import Minio
import json
from functools import partial
from multiprocessing.dummy import Pool as ThreadPool
import requests
import urllib3
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Create AWS resource and client
# s3 = boto3.resource('s3')
# s3_client = boto3.client('s3')
# lambda_client = boto3.client('lambda')

wsk_host= "10.150.21.197"
access_key = ''
secret_key = ''
endpoint = ''

def invoke(action, payload):
    url = f"https://{wsk_host}/api/v1/namespaces/guest/actions/{action}?blocking=true"

    headers = {
      'Content-Type': 'application/json',
      'Authorization': 'Basic MjNiYzQ2YjEtNzFmNi00ZWQ1LThjNTQtODE2YWE0ZjhjNTAyOjEyM3pPM3haQ0xyTU42djJCS0sxZFhZRnBYbFBrY2NPRnFtMTJDZEFzTWdSVTRWck5aOWx5R1ZDR3VNREdJd1A='
    }
    response = requests.post(url, headers=headers, data=payload, verify=False)

    return response.json()['response']

total_map = 0
total_network = 0


def map_invoke_lambda(job_bucket, bucket, all_keys, batch_size, mapper_id):
    keys = all_keys[int(mapper_id * batch_size): int((mapper_id + 1) * batch_size)]
    key = ""
    for item in keys:
        key += item + '/'
    key = key[:-1]

    response = invoke(
        action='mapper',
        payload=json.dumps({
            "job_bucket": job_bucket,
            "bucket": bucket,
            "keys": key,
            "mapper_id": mapper_id,
            "endpoint": endpoint,
            "access_key": access_key,
            "secret_key": secret_key
        })
    )

    json_data = response['result']

    global total_map, total_network
    total_map += float(json_data['map'])
    total_network += float(json_data['network'])


def reduce_invoke_lambda(job_bucket):
    response = invoke(
        action='reducer',
        payload=json.dumps({
            "job_bucket": job_bucket,
            "endpoint": endpoint,
            "access_key": access_key,
            "secret_key": secret_key
        })
    )
    return response['result']


def main(args):
    src_bucket = args['src_bucket']
    n_mapper = args['n_mapper']
    n_data = args['n_data']
    job_bucket = args['job_bucket']

    global access_key, secret_key, endpoint
    access_key = args['access_key']
    secret_key = args['secret_key']
    endpoint = args['endpoint']

    minio_client = Minio(endpoint=endpoint,
                    access_key=access_key,
                    secret_key=secret_key,
                    secure=False)

    found = minio_client.bucket_exists(src_bucket)
    if not found:
        print(f'Bucket {src_bucket} does not exist!')

    # Fetch all the keys
    all_data = []
    for obj in minio_client.list_objects(bucket_name=src_bucket, recursive=True):
        all_data.append(obj.object_name)
        if len(all_data) == n_data:
            break


    print("dataset file: " + str(len(all_data)))
    print("data name: " + str(all_data))

    print("# of Mappers: ", n_mapper)
    total_size = len(all_data)
    batch_size = 0

    if total_size % n_mapper == 0:
        batch_size = int(total_size / n_mapper)
    else:
        batch_size = int(total_size // n_mapper + 1)

    for idx in range(n_mapper):
        print(f"mapper-{idx}: {all_data[idx * batch_size: (idx + 1) * batch_size]}")

    pool = ThreadPool(n_mapper)
    invoke_lambda_partial = partial(map_invoke_lambda, job_bucket, src_bucket, all_data, batch_size)
    pool.map(invoke_lambda_partial, range(n_mapper))
    pool.close()
    pool.join()

    while True:
        job_keys = list(minio_client.list_objects(bucket_name=job_bucket))
        print("Wait Mapper Jobs ...")
        time.sleep(5)
        if len(job_keys) == n_mapper:
            print(f"[*] Map Done : mapper {n_mapper} finished.")
            break

    print("[*] Map Done - map : " + str(total_map) + " network : " + str(total_network))

    # Reducer
    res = reduce_invoke_lambda(job_bucket)
    print("[*] Reduce Done : reducer finished.")

    return {'map': f'map: {total_map}s, network: {total_network}s', 'reduce': f'reduce: {res["reduce"]}s, network: {res["reduce"]}s'}


if __name__ == '__main__':
    main({'src_bucket': 'mapreduce', 'n_mapper': 10, 'n_data': 30, 'job_bucket': 'jobbucket',
        'endpoint': '10.150.21.197:9002', 'access_key': 'minioadmin', 'secret_key': 'minioadmin'})
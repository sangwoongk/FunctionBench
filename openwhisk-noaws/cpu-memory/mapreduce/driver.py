from minio import Minio
import json
from functools import partial
from multiprocessing.dummy import Pool as ThreadPool
import requests
import urllib3
import time
import random

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Create AWS resource and client
# s3 = boto3.resource('s3')
# s3_client = boto3.client('s3')
# lambda_client = boto3.client('lambda')

wsk_host= '10.150.3.42'
access_key = ''
secret_key = ''
endpoint = ''

def access_db(activ_id):
    db_host = '10.150.3.42'
    db_port = '5984'
    db_usr = 'admin'
    db_password = 'password'
    url = f'http://{db_host}:{db_port}/whisk_local_activations/_find'

    res = requests.post(url=url, json={
        'selector': {
            'activationId': activ_id
        },
        'fields': ['activationId', 'duration', 'annotations', 'response']
	}, auth=(db_usr, db_password))

    doc = json.loads(res.text)['docs']
    return doc


def check_activation(activ_id, wait, wait_time):
    ret = None
    start = time.time()
    while True:
        if time.time() - start > wait_time:
            break

        temp = access_db(activ_id)
        if len(temp) == 0:
            time.sleep(wait)
        else:
            ret = temp[0]
            break

    return ret


def invoke(action, payload):
    url = f"https://{wsk_host}/api/v1/namespaces/guest/actions/{action}"

    wsk_auth = '23bc46b1-71f6-4ed5-8c54-816aa4f8c502:123zO3xZCLrMN6v2BKK1dXYFpXlPkccOFqm12CdAsMgRU4VrNZ9lyGVCGuMDGIwP'
    auth = tuple(wsk_auth.split(':'))
    response = requests.post(url=url, auth=auth, json=payload, params={'blocking': 'true'}, verify=False)

    return response.status_code, response.json()



total_map = 0
total_network = 0
total_decode = 0


def map_invoke_lambda(job_bucket, bucket, all_keys, batch_size, mapper_id):
    keys = all_keys[int(mapper_id * batch_size): int((mapper_id + 1) * batch_size)]
    key = ""
    for item in keys:
        key += item + '/'
    key = key[:-1]

    status, response = invoke(
        action='mapper',
        payload={
            "job_bucket": job_bucket,
            "bucket": bucket,
            "keys": key,
            "mapper_id": mapper_id,
            "endpoint": endpoint,
            "access_key": access_key,
            "secret_key": secret_key
        }
    )

    json_data = None
    if status == 200:
        json_data = response['response']['result']
    elif status == 202:
        data = check_activation(response['activationId'], 5, 300)
        json_data = data['response']['result']
    else:
        print(f'status code: {status}')
        return

    if json_data == None:
        print(f'there is no activation!')
        return

    print(json_data)
    global total_map, total_network, total_decode
    total_map += float(json_data['map'])
    total_network += float(json_data['network'])
    total_decode += float(json_data['decode'])


def reduce_invoke_lambda(job_bucket):
    _, response = invoke(
        action='reducer',
        payload={
            "job_bucket": job_bucket,
            "endpoint": endpoint,
            "access_key": access_key,
            "secret_key": secret_key
        }
    )
    return response['response']['result']


def main(args):
    src_bucket = args['src_bucket']
    n_mapper = args['n_mapper']
    n_data = args['n_data']
    job_bucket = args['job_bucket']

    global access_key, secret_key, endpoint
    access_key = args['access_key']
    secret_key = args['secret_key']
    endpoint = args['endpoint']

    global total_map, total_network, total_decode
    total_map = 0
    total_network = 0
    total_decode = 0

    minio_client = Minio(endpoint=endpoint,
                    access_key=access_key,
                    secret_key=secret_key,
                    secure=False)

    found = minio_client.bucket_exists(src_bucket)
    if not found:
        print(f'Bucket {src_bucket} does not exist!')

    all_data = []
    objects = list(minio_client.list_objects(bucket_name=src_bucket, recursive=True))

    picks = None
    if n_data == -1:
        # Fetch all data
        picks = objects
    else:
        # Pick n_data data randomly
        picks = random.choices(objects, k=n_data)

    for obj in picks:
        all_data.append(obj.object_name)


    print("dataset file: " + str(len(all_data)))
    # print("data name: " + str(all_data))

    print("# of Mappers: ", n_mapper)
    total_size = len(all_data)
    batch_size = 0

    if total_size % n_mapper == 0:
        batch_size = int(total_size / n_mapper)
    else:
        batch_size = int(total_size // n_mapper + 1)

    '''
    for idx in range(n_mapper):
        print(f"mapper-{idx}: {all_data[idx * batch_size: (idx + 1) * batch_size]}")
    '''

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

    print("[*] Map Done - map : " + str(total_map) + " network : " + str(total_network) + " decode : " + str(total_decode))

    # Reducer
    res = reduce_invoke_lambda(job_bucket)
    print("[*] Reduce Done : reducer finished.")

    return {'map': f'map: {total_map}s, network: {total_network}s, decode: {total_decode}s',
            'reduce': f'reduce: {res["reduce"]}s, network: {res["network"]}s, decode: {res["decode"]}s'}


if __name__ == '__main__':
    main({'src_bucket': 'mapreduce', 'n_mapper': 10, 'n_data': 400, 'job_bucket': 'jobbucket',
        'endpoint': '10.150.21.197:9002', 'access_key': 'minioadmin', 'secret_key': 'minioadmin'})
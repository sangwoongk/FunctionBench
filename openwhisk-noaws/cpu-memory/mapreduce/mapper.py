import json
from minio import Minio
from time import time
import io


subs = "</title><text>"
computer_language = ["JavaScript", "Java", "PHP", "Python", "C#", "C++",
                     "Ruby", "CSS", "Objective-C", "Perl",
                     "Scala", "Haskell", "MATLAB", "Clojure", "Groovy"]


def main(args):
    job_bucket = args['job_bucket']
    src_bucket = args['bucket']
    src_keys = args['keys']
    mapper_id = args['mapper_id']

    access_key = args['access_key']
    secret_key = args['secret_key']
    endpoint = args['endpoint']

    minio_client = Minio(endpoint=endpoint,
                    access_key=access_key,
                    secret_key=secret_key,
                    secure=False)

    output = {}

    for lang in computer_language:
        output[lang] = 0

    network = 0
    map = 0
    decode = 0
    keys = src_keys.split('/')

    # Download and process all keys
    for key in keys:
        print(key)
        start = time()
        raw = None
        try:
            response = minio_client.get_object(bucket_name=src_bucket, object_name=key)
            raw = response.data
        finally:
            response.close()
            response.release_conn()
        network += time() - start

        start = time()
        data = list(eval(raw.decode()))
        decode += time() - start

        start = time()
        for line in data:
            text = line['text']
            for lang in computer_language:
                if lang in text:
                    output[lang] += 1

        map += time() - start

    metadata = {
        'output': str(output),
        'network': str(network),
        'map': str(map),
        'decode': str(decode)
    }
    print(metadata)

    start = time()
    json_data = json.dumps(output).encode('utf-8')
    byte_data = io.BytesIO(json_data)
    minio_client.put_object(bucket_name=job_bucket, object_name=str(mapper_id), data=byte_data, length=-1, part_size=5*1024*1024, metadata=metadata)
    network += time() - start

    return metadata

if __name__ == '__main__':
    main({'job_bucket': 'jobbucket', 'bucket': 'mapreduce', 'mapper_id': 0, 
          'keys': '00c2bfc7-57db-496e-9d5c-d62f8d8119e3.json/00e58afe-3ef5-42a6-92f3-8ee7abf868e1.json/0104b39c-7aa4-45cd-8d28-b05dc6bafdf2.json',
          'endpoint': '10.150.21.197:9002', 'access_key': 'minioadmin', 'secret_key': 'minioadmin'})
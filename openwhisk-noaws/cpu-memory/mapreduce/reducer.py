import json
from minio import Minio
from time import time


computer_language = ["JavaScript", "Java", "PHP", "Python", "C#", "C++",
                     "Ruby", "CSS", "Objective-C", "Perl",
                     "Scala", "Haskell", "MATLAB", "Clojure", "Groovy"]


def main(args):
    job_bucket = args['job_bucket']
    access_key = args['access_key']
    secret_key = args['secret_key']
    endpoint = args['endpoint']

    output = {}

    for lang in computer_language:
        output[lang] = 0

    network = 0
    reduce = 0

    minio_client = Minio(endpoint=endpoint,
                    access_key=access_key,
                    secret_key=secret_key,
                    secure=False)
    all_keys = []
    for obj in minio_client.list_objects(bucket_name=job_bucket, recursive=True):
        all_keys.append(obj.object_name)

    for key in all_keys:
        start = time()
        raw = None
        try:
            response = minio_client.get_object(bucket_name=job_bucket, object_name=key)
            raw = response.data.decode()
        finally:
            response.close()
            response.release_conn()
 
        network += time() - start

        start = time()
        data = json.loads(raw)
        for key in data:
            output[key] += data[key]
        reduce += time() - start

    metadata = {
        'output': str(output),
        'network': str(network),
        'reduce': str(reduce)
    }

    return metadata

if __name__ == '__main__':
    main({'job_bucket': 'jobbucket',
        'endpoint': '10.150.21.197:9002', 'access_key': 'minioadmin', 'secret_key': 'minioadmin'})
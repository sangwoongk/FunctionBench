from minio import Minio
from sklearn.feature_extraction.text import TfidfVectorizer
import joblib
import pandas as pd
from time import time
import os
import re

tmp = '/tmp/'
cleanup_re = re.compile('[^a-z]+')


def cleanup(sentence):
    sentence = sentence.lower()
    sentence = cleanup_re.sub(' ', sentence).strip()
    return sentence


def main(args):
    x = args['x']
    access_key = args['access_key']
    secret_key = args['secret_key']
    endpoint = args['endpoint']

    minio_client = Minio(endpoint=endpoint,
                    access_key=access_key,
                    secret_key=secret_key,
                    secure=False)

    dataset_object_key = args['dataset_name']
    dataset_bucket = args['dataset_bucket']

    model_object_key = args['model_name']  # example : lr_model.pk
    model_bucket = args['model_bucket']

    model_path = tmp + model_object_key
    if not os.path.isfile(model_path):
        minio_client.fget_object(bucket_name=model_bucket, object_name=model_object_key, file_path=model_path)

    dataset_path = tmp + dataset_object_key
    if not os.path.isfile(dataset_path):
        minio_client.fget_object(bucket_name=dataset_bucket, object_name=dataset_object_key, file_path=dataset_path)

    dataset = pd.read_csv(dataset_path)

    start = time()

    df_input = pd.DataFrame()
    df_input['x'] = [x]
    df_input['x'] = df_input['x'].apply(cleanup)

    dataset['train'] = dataset['Text'].apply(cleanup)

    tfidf_vect = TfidfVectorizer(min_df=100).fit(dataset['train'])

    X = tfidf_vect.transform(df_input['x'])

    model = joblib.load(model_path)
    y = list(model.predict(X))

    latency = time() - start
    os.remove(dataset_path)
    os.remove(model_path)
    return {'y': str(y), 'latency': latency}

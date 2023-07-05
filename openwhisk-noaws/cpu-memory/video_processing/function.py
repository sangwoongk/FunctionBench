from minio import Minio
from time import time
import cv2 

tmp = "/tmp/"
FILE_NAME_INDEX = 0
FILE_PATH_INDEX = 2

def video_processing(object_key, video_path):
    file_name = object_key.split(".")[FILE_NAME_INDEX]
    result_file_path = tmp+file_name+'-output.avi'

    video = cv2.VideoCapture(video_path)

    width = int(video.get(3))
    height = int(video.get(4))

    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(result_file_path, fourcc, 20.0, (width, height))

    start = time()
    while video.isOpened():
        ret, frame = video.read()

        if ret:
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            tmp_file_path = tmp+'tmp.jpg'
            cv2.imwrite(tmp_file_path, gray_frame)
            gray_frame = cv2.imread(tmp_file_path)
            out.write(gray_frame)
        else:
            break

    latency = time() - start

    video.release()
    out.release()
    return latency, result_file_path

def main(event):
    latencies = {}
    timestamps = {}
    
    timestamps['starting_time'] = time()
    bucket = event['bucket']
    access_key = event['access_key']
    secret_key = event['secret_key']
    endpoint = event['endpoint']

    minio_client = Minio(endpoint=endpoint,
                    access_key=access_key,
                    secret_key=secret_key,
                    secure=False)

    found = minio_client.bucket_exists(bucket)
    if not found:
        print(f'Bucket {bucket} does not exist!')

    vid_name = event['video']
    vid_path = f'/tmp/{vid_name}'

    start = time()
    minio_client.fget_object(bucket_name=bucket, object_name=vid_name, file_path=vid_path)
    download_latency = time() - start

    latencies['download_data'] = download_latency

    video_processing_latency, upload_path = video_processing(vid_name, vid_path)
    latencies['function_execution'] = video_processing_latency

    '''
    start = time()
    s3_client.upload_file(upload_path, output_bucket, upload_path.split("/")[FILE_PATH_INDEX])
    upload_latency = time() - start
    latencies["upload_data"] = upload_latency
    timestamps["finishing_time"] = time()
    '''

    return {'latencies': latencies, 'timestamps': timestamps}
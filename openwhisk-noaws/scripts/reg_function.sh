#!/bin/bash

minio_img='caslabdgist/minio_python:0.1'

# mapreduce
dir='../cpu-memory/mapreduce'
wsk -i action update driver ${dir}/driver.py --docker $minio_img --timeout 300000 --memory 512
wsk -i action update mapper ${dir}/mapper.py --docker $minio_img --timeout 300000 --memory 512
wsk -i action update reducer ${dir}/reducer.py --docker $minio_img --timeout 300000 --memory 512

# video processing
dir='../cpu-memory/video_processing'
wsk -i action update video_process ${dir}/function.py --docker $minio_img --timeout 300000 --memory 512

# cnn classification
dir='../cpu-memory/model_serving/cnn_image_classification'
ml_img='caslabdgist/tf:0.1'
wsk -i action update cnn ${dir}/__main__.py --docker $ml_img --timeout 300000 --memory 512


# lr prediction
dir='../cpu-memory/model_serving/ml_lr_prediction'
ml_img='caslabdgist/lr:0.1'
wsk -i action update lr ${dir}/ml_lr_prediction.py --docker $ml_img --timeout 300000 --memory 512

#!/bin/bash

minio_img='minio_python:0.1'

# mapreduce
dir='../cpu-memory/mapreduce'
wsk -i action update driver ${dir}/driver.py --docker $minio_img --timeout 300000 --memory 512
wsk -i action update mapper ${dir}/mapper.py --docker $minio_img --timeout 300000 --memory 512
wsk -i action update reducer ${dir}/reducer.py --docker $minio_img --timeout 300000 --memory 512

# video processing
dir='../cpu-memory/video_processing'
wsk -i action update video_process ${dir}/function.py --docker $minio_img --timeout 300000 --memory 512
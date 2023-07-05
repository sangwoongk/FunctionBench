#!/bin/bash
wsk -i action update driver driver.py --docker minio_python:0.1 --timeout 300000 --memory 512
wsk -i action update mapper mapper.py --docker minio_python:0.1 --timeout 300000 --memory 512
wsk -i action update reducer reducer.py --docker minio_python:0.1 --timeout 300000 --memory 512

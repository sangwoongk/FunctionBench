#!/bin/bash
wsk -i action update video_process function.py --docker minio_python:0.1 --timeout 300000 --memory 512

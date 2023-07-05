#!/bin/bash
wsk -i action invoke video_process --blocking -p bucket openwhisk -p access_key minioadmin -p secret_key minioadmin -p endpoint 10.150.21.197:9002 -p video SampleVideo_1280x720_30mb.mp4

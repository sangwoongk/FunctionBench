#!/bin/bash
mapper=$1
data=$2

if [ -z "$mapper" ]
then
	mapper=10
fi

if [ -z "$data" ]
then
	data=40
fi

wsk -i action invoke driver --blocking -p src_bucket mapreduce -p n_mapper $mapper -p n_data $data -p job_bucket jobbucket -p endpoint 10.150.21.197:9002 -p access_key minioadmin -p secret_key minioadmin

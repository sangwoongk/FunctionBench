#!/bin/bash
for i in {1..10}
do
	# pull data
	#wget https://dumps.wikimedia.org/enwiki/20230701/enwiki-20230701-abstract${i}.xml.gz -P /data1/mapreduce

	# unzip data
	gzip -d /data1/mapreduce/enwiki-20230701-abstract${i}.xml.gz
done

import subprocess
import argparse
import time
import json

def cmd(line):
	ret = subprocess.check_output(line, shell=True).decode()
	return ret


def redeploy_ow():
	line = 'cd ~/workspace/openwhisk-numa/ansible; ./redeploy_ow.sh'
	print(line)
	cmd(line)

def auto_mapreduce():
	param = ['5 30', '5 50', '5 150']
	numa = ['0-9 0', '0-9 1']
	iter = 7

	for config in param:
		for node in numa:
			# warmup functions
			command = f'python3 invoke_action_numa.py -t mapreduce -p {config}'
			print(command)

			cmd(command)
			time.sleep(10)

			for i in range(iter):
				command = f'python3 invoke_action_numa.py -t mapreduce -p {config} -n {node}'
				print(command)
				result = cmd(command)
				print(result)

				time.sleep(20)

		redeploy_ow()
		time.sleep(10)



parser = argparse.ArgumentParser()
parser.add_argument('--type', '-t', type=str, required=True)

args = parser.parse_args()
action_type = args.type

if action_type == 'mapreduce':
	auto_mapreduce()

import argparse
import urllib3
import requests
import subprocess
import time
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def ssh(cmd):
	ssh = f'ssh -p 20022 caslab@10.150.21.197 "{cmd}"'
	ret = subprocess.check_output(ssh, shell=True).decode()
	return ret


def command(cmd):
	ret = subprocess.check_output(cmd, shell=True).decode()
	return ret


def access_db(activ_id):
	db_host = '10.150.3.42'
	db_port = '5984'
	db_usr = 'admin'
	db_password = 'password'
	url = f'http://{db_host}:{db_port}/whisk_local_activations/_find'

	res = requests.post(url=url, json={
		'selector': {
			'activationId': activ_id
		},
		'fields': ['activationId', 'duration', 'annotations', 'response']
	}, auth=(db_usr, db_password))

	doc = json.loads(res.text)['docs']
	return doc


def check_activation(activ_id, wait, wait_time):
	ret = None
	start = time.time()
	while True:
		if time.time() - start > wait_time:
			break

		temp = access_db(activ_id)
		if len(temp) == 0:
			time.sleep(wait)
		else:
			ret = temp[0]
			break

	return ret


def invoke_action(action, params):
	wsk_host = '10.150.3.42'
	url = f'https://{wsk_host}/api/v1/namespaces/guest/actions/{action}'
	wsk_auth = '23bc46b1-71f6-4ed5-8c54-816aa4f8c502:123zO3xZCLrMN6v2BKK1dXYFpXlPkccOFqm12CdAsMgRU4VrNZ9lyGVCGuMDGIwP'
	auth = tuple(wsk_auth.split(':'))
	blocking = 'true'
	result = 'false'

	response = requests.post(url=url, json=params, auth=auth, params={'blocking': blocking, 'result': result}, verify=False)
	print(f'response status: {response.status_code}')
	resp_json = response.json()

	return resp_json['activationId']


'''
	param[0]: n_mapper
	param[1]: n_data
	param[2]: src_bucket
	param[3]: job_bucket
'''
def invoke_mapreduce(input):
	params = {}
	params['endpoint'] = '10.150.21.197:9002'
	params['access_key'] = 'minioadmin'
	params['secret_key'] = 'minioadmin'
	params['src_bucket'] = 'mapreduce'
	params['job_bucket'] = 'jobbucket'

	if len(input) == 0:
		params['n_mapper'] = 10
		params['n_data'] = 30
	elif len(input) < 3:
		params['n_mapper'] = int(input[0])
		params['n_data'] = int(input[1])
	else:
		params['n_mapper'] = int(input[0])
		params['n_data'] = int(input[1])
		params['src_bucket'] = input[2]
		params['job_bucket'] = input[3]

	print(f'n_mapper: {params["n_mapper"]}, n_data: {params["n_data"]}')

	req_id = invoke_action('driver', params)
	data = check_activation(req_id, 5, 300)
	ret = {
		'activationId': data['activationId'],
		'duration': data['duration'] / 1000,
		'result': data['response']['result']
	}
	print(ret)
	# print(f'activationId: {data["activationId"]}, duration: {data["duration"]/1000}s, result: {data["response"]["result"]}')


def invoke_cnn():
	params = {}
	params['endpoint'] = '10.150.21.197:9002'
	params['access_key'] = 'minioadmin'
	params['secret_key'] = 'minioadmin'

	params['input_bucket'] = 'openwhisk'
	params['model_bucket'] = 'openwhisk'

	params['input_name'] = 'animal-dog.jpg'
	params['model_name'] = 'squeezenet_weights_tf_dim_ordering_tf_kernels.h5'

	req_id = invoke_action('cnn', params)
	data = check_activation(req_id, 5, 300)
	ret = {
		'activationId': data['activationId'],
		'duration': data['duration'] / 1000,
		'result': data['response']['result']
	}
	print(ret)

'''
	numa[0]: cpunode
	numa[1]: memnode
'''
def change_numanode(numa, targets):
	name_cmd = "docker ps --format '{{.Names}}'"
	names = ssh(name_cmd).split()

	for name in names:
		for target in targets:
			if target in name:
				update_cmd = f'docker update {name} --cpuset-cpus {numa[0]} --cpuset-mems {numa[1]}'
				ssh(update_cmd)


parser = argparse.ArgumentParser()
parser.add_argument('--type', '-t', type=str, required=True)
parser.add_argument('--param', '-p', nargs='+', default=[])
parser.add_argument('--numa', '-n', nargs='+', default=[], help='[0]: cpunode, [1]: memnode')

args = parser.parse_args()
action_type = args.type
param = args.param
numa = args.numa

if action_type == 'mapreduce':
	if len(numa) != 0:
		change_numanode(numa, ['driver', 'mapper', 'reducer'])
		time.sleep(5)
	invoke_mapreduce(param)
elif action_type == 'cnn':
	if len(numa) != 0:
		change_numanode(numa, ['cnn'])
		time.sleep(5)
	invoke_cnn()
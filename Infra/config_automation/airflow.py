import os
import paramiko
import yaml

yaml_file_path = "/usr/local/Big-Data-Platform/Infra/environmentvariables.yaml"

with open(yaml_file_path, 'r') as yaml_file:
    config = yaml.safe_load(yaml_file)

hostnames = config['hostnames']

hosturls = config['hosturls']

number_of_nodes= config['general']['number_of_nodes']

database = config['mysql']['airflowdatabase']
username = config['mysql']['username']
password = config['mysql']['password']

def update_airflow_cfg(hostname, directory):
    with open(config['airflow']['conf_path']+'airflow.cfg', 'r') as file:
        lines = file.readlines()

    # # remove all lines containing server
    # filtered_lines = [line for line in lines if 'zookeeper_quorum' not in line and '[zookeeper]' not in line and 'celery_broker_url' not in line and 'celery_result_backend' not in line]

    # if number_of_nodes > 1 :
    #     zookeeper_nodes = [f'{h}:2181' for h in hostnames.keys()]
    #     zookeeper_string = ','.join(zookeeper_nodes)
    #     zookeeper_quorum = f'zookeeper_quorum = {zookeeper_string}\n'
    #     filtered_lines.append('\n[zookeeper]\n')
    #     filtered_lines.append(zookeeper_quorum)

    for i, line in enumerate(lines):
        if 'executor = ' in line:
            lines[i] = f'executor = CeleryExecutor\n'
        elif 'sql_alchemy_conn = ' in line:
            lines[i] = f'sql_alchemy_conn = mysql+mysqlconnector://{username}:{password}@master-node:3306/{database}\n'
        elif 'broker_url = ' in line:
            lines[i] = f'broker_url = redis://master-node:6379/0\ncelery_broker_url = redis://master-node:6379/0\ncelery_result_backend = redis://master-node:6379/0\n'
        elif 'web_server_port =' in line:
            lines[i] = f'web_server_port = 8181\n'

    # lines = filtered_lines

    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # SSH connection details for the external machine
    remote_host = hosturls[hostname]
    remote_port = config['ssh']['remote_port']
    remote_username = config['ssh']['remote_username']
    private_key_path = config['ssh']['private_key_path']

    try:
        private_key = paramiko.RSAKey.from_private_key_file(private_key_path)
        ssh_client.connect(remote_host, port=remote_port, username=remote_username, pkey=private_key)
        sftp = ssh_client.open_sftp()
        remote_path = os.path.join(directory, 'airflow.cfg')
        with sftp.file(remote_path, 'w') as remote_file:
            remote_file.write(''.join(lines))  # Concatenate lines into a single string

        print(f"File saved to {remote_host}:{remote_path}")
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        sftp.close()
        ssh_client.close()

# Loop through hostnames and update the properties file for each one
for hostname, directory in hostnames.items():
    if "master" in hostname:
        directory = config['airflow']['conf_path']
        update_airflow_cfg(hostname, directory)


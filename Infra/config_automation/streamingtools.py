import os
import paramiko
import yaml

yaml_file_path = "/usr/local/Big-Data-Platform/Infra/environmentvariables.yaml"

with open(yaml_file_path, 'r') as yaml_file:
    config = yaml.safe_load(yaml_file)

hostnames = config['hostnames']
hosturls = config['hosturls']

number_of_nodes= config['general']['number_of_nodes']

def update_myid(hostname, directory):
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
        remote_path = os.path.join(directory, 'myid')
        ssh_client.exec_command(f"rm -r {directory}") 
        ssh_client.exec_command(f"mkdir -p {directory}") 
        ssh_client.exec_command(f"echo {list(hostnames).index(hostname)+1} >> {remote_path}")

        print(f"File saved to {remote_host}:{remote_path}")
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        sftp.close()
        ssh_client.close()

def update_zookeeper_properties(hostname, directory):
    myid_path = config['general']['hadoop_cluster']+config['kafka']['myid_path']
    with open(config['general']['hadoop_cluster']+config['kafka']['conf_path']+'zookeeper.properties', 'r') as file:
        lines = file.readlines()

    # remove all lines containing server
    filtered_lines = [line for line in lines if 'server.' not in line and 'initLimit' not in line and 'syncLimit' not in line]

    # if the number of nodes = 1 , we don't need server string in the file
    if number_of_nodes > 1 :
        filtered_lines.append('initLimit=10\n')
        filtered_lines.append('syncLimit=5\n')
        filtered_lines.append('server.1=master-node:2888:3888\n')

        for i in range(2,number_of_nodes+1):
            server_string = f"server.{i}=slave-node{i-1}:2888:3888\n"
            filtered_lines.append(server_string)

    for i, line in enumerate(filtered_lines):
        if line.startswith("dataDir"):
            filtered_lines[i] = f'dataDir={myid_path}\n'

    lines = filtered_lines

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
        remote_path = os.path.join(directory, 'zookeeper.properties')
        with sftp.file(remote_path, 'w') as remote_file:
            remote_file.write(''.join(lines))  # Concatenate lines into a single string

        print(f"File saved to {remote_host}:{remote_path}")
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        sftp.close()
        ssh_client.close()

def update_server_properties(hostname, directory):
    with open(config['general']['hadoop_cluster']+config['kafka']['conf_path']+'server.properties', 'r') as file:
        lines = file.readlines()
    for i, line in enumerate(lines):
        if line.startswith("#listeners"):
            lines[i] = f'listeners=PLAINTEXT://{hostname}:9092\n'

        elif line.startswith("#advertised.listeners"):
            lines[i] = f'advertised.listeners=PLAINTEXT://{hostname}:9092\n'

        elif line.startswith("listeners=PLAINTEXT://"):
            lines[i] = f'listeners=PLAINTEXT://{hostname}:9092\n'

        elif line.startswith("advertised.listeners=PLAINTEXT://"):
            lines[i] = f'advertised.listeners=PLAINTEXT://{hostname}:9092\n'

        elif 'broker.id' in line:
            lines[i] = f'broker.id={list(hostnames).index(hostname)+1}\n'
        elif 'zookeeper.connect=' in line:
            zookeeper_nodes = [f'{h}:2181' for h in hostnames.keys()]
            zookeeper_string = ','.join(zookeeper_nodes)
            lines[i] = f'zookeeper.connect={zookeeper_string}\n'

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
        remote_path = os.path.join(directory, 'server.properties')
        with sftp.file(remote_path, 'w') as remote_file:
            remote_file.write(''.join(lines))  # Concatenate lines into a single string

        print(f"File saved to {remote_host}:{remote_path}")
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        sftp.close()
        ssh_client.close()

def update_nifi_properties(hostname, directory):
    with open(config['general']['hadoop_cluster']+config['nifi']['conf_path']+'nifi.properties', 'r') as file:
        lines = file.readlines()

    zookeeper_nodes = [f'{h}:2181' for h in hostnames.keys()]
    zookeeper_string = ','.join(zookeeper_nodes)
    # Define the dictionary
    replace_dict = {
        'nifi.remote.input.host': f'nifi.remote.input.host={hostname}\n',
        'nifi.remote.input.secure': 'nifi.remote.input.secure=false\n',
        'nifi.remote.input.socket.port': 'nifi.remote.input.socket.port=9998\n',
        'nifi.web.http.port': 'nifi.web.http.port=8888\n',
        'nifi.web.http.host': f'nifi.web.http.host={hostname}\n',
        'nifi.web.https.host': 'nifi.web.https.host=\n',
        'nifi.web.https.port': 'nifi.web.https.port=\n',
        'nifi.web.https.application.protocols=http/1.1': '# nifi.web.https.application.protocols=http/1.1\n',
        'nifi.cluster.is.node': 'nifi.cluster.is.node=true\n',
        'nifi.cluster.node.address': f'nifi.cluster.node.address={hostname}\n',
        'nifi.cluster.node.protocol.port': 'nifi.cluster.node.protocol.port=7474\n',
        'nifi.cluster.load.balance.host': f'nifi.cluster.load.balance.host={hostname}\n',
        'nifi.zookeeper.connect.string': f'nifi.zookeeper.connect.string={zookeeper_string}\n',
        'nifi.sensitive.props.key=': 'nifi.sensitive.props.key=GTfOUQvFqGuMyQ7Q20cL1KkpvyBhIbCe\n',
        'nifi.security.keystore=': lambda line: line.split("=")[0] + '=\n',
        'nifi.security.keystoreType=': lambda line: line.split("=")[0] + '=\n',
        'nifi.security.keystorePasswd=': lambda line: line.split("=")[0] + '=\n',
        'nifi.security.keyPasswd=': lambda line: line.split("=")[0] + '=\n',
        'nifi.security.truststore=': lambda line: line.split("=")[0] + '=\n',
        'nifi.security.truststoreType=': lambda line: line.split("=")[0] + '=\n',
        'nifi.security.truststorePasswd=': lambda line: line.split("=")[0] + '=\n',
        'nifi.zookeeper.auth.type': 'nifi.zookeeper.auth.type=default\n'
    }

    # Loop through the lines
    for i, line in enumerate(lines):
        for key, value in replace_dict.items():
            if key in line:
                if callable(value):
                    lines[i] = value(line)
                else:
                    lines[i] = value
                break

    filtered_lines = [line for line in lines if 'nifi.web.api.enabled' not in line]
    filtered_lines.append("nifi.web.api.enabled=true")
    lines = filtered_lines

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
        remote_path = os.path.join(directory, 'nifi.properties')
        with sftp.file(remote_path, 'w') as remote_file:
            remote_file.write(''.join(lines))  # Concatenate lines into a single string

        print(f"File saved to {remote_host}:{remote_path}")
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        sftp.close()
        ssh_client.close()

def update_state_management(hostname, directory):
    with open(config['general']['hadoop_cluster']+config['nifi']['conf_path']+'state-management.xml', 'r') as file:
        lines = file.readlines()


    for i, line in enumerate(lines):

        if '<property name="Connect String">' in line:
                zookeeper_nodes = [f'{h}:2181' for h in hostnames.keys()]
                zookeeper_string = ','.join(zookeeper_nodes)
                lines[i] = f'        <property name="Connect String">{zookeeper_string}</property>\n'

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
        remote_path = os.path.join(directory, 'state-management.xml')
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
    directory = config['general']['hadoop_cluster']+config['kafka']['myid_path']
    update_myid(hostname, directory)
    directory = config['general']['hadoop_cluster']+config['kafka']['conf_path']
    update_zookeeper_properties(hostname, directory)
    update_server_properties(hostname, directory)
    directory = config['general']['hadoop_cluster']+config['nifi']['conf_path']
    update_nifi_properties(hostname, directory)
    update_state_management(hostname, directory)
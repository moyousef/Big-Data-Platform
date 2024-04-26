import os
import paramiko
import yaml

yaml_file_path = "/usr/local/Big-Data-Platform/Infra/environmentvariables.yaml"

with open(yaml_file_path, 'r') as yaml_file:
    config = yaml.safe_load(yaml_file)

hostnames = config['hostnames']
hosturls = config['hosturls']
username = config['ssh']['remote_username']

def update_ranger_ugsync_site_xml(hostname, directory):
    with open( directory +'ranger-ugsync-site.xml', 'r') as file:
        lines = file.readlines()

    replace_dict = {
        '<name>ranger.usersync.enabled</name>': f'                <value>true</value>\n',
        '<name>ranger.usersync.ssl</name>': f'                <value>false</value>\n',
    }

    for i, line in enumerate(lines):
        for key, value in replace_dict.items():
            if key in line:
                if callable(value):
                    lines[i] = value(line)
                else:
                    lines[i] = value
                break

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
        remote_path = os.path.join(directory, 'ranger-ugsync-site.xml')
        with sftp.file(remote_path, 'w') as remote_file:
            remote_file.write(''.join(lines))  # Concatenate lines into a single string

        print(f"File saved to {remote_host}:{remote_path}")
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        sftp.close()
        ssh_client.close()

def update_ranger_ugsync_default_xml(hostname, directory,hadoop_home):
    with open( directory +'ranger-ugsync-default.xml', 'r') as file:
        lines = file.readlines()

    replace_dict = {
        '<name>ranger.usersync.ssl</name>': f'                <value>false</value>\n',
        '<name>ranger.usersync.enabled</name>': f'                <value>true</value>\n',
    }

    for i, line in enumerate(lines):
        for key, value in replace_dict.items():
            if key in line:
                if callable(value):
                    lines[i+1] = value(line)
                else:
                    lines[i+1] = value
                break

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
        remote_path = os.path.join(directory, 'ranger-ugsync-default.xml')
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
        directory = config['general']['hadoop_cluster']+config['ranger']['ranger_usersync'] + "conf/"
        update_ranger_ugsync_site_xml(hostname, directory)
        update_ranger_ugsync_default_xml(hostname, directory)
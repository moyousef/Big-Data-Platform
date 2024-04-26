import os
import paramiko
import yaml

yaml_file_path = "/usr/local/Big-Data-Platform/Infra/environmentvariables.yaml"

with open(yaml_file_path, 'r') as yaml_file:
    config = yaml.safe_load(yaml_file)

# Create a list of hostnames and corresponding directories
hostnames = config['hostnames']
hosturls = config['hosturls']

database = config['mysql']['hivedatabase']
username = config['mysql']['username']
password = config['mysql']['password']

exist = []
java_home = config['java']['home']

def update_hive_env(java_home, directory):
    with open(config['general']['hadoop_cluster']+config['hive']['conf_path']+'hive-env.sh', 'r') as file:
        lines = file.readlines()

    for i, line in enumerate(lines):
        if line.startswith("export JAVA_HOME"):
            lines[i] = f'export JAVA_HOME={java_home}\n'
            exist.append(1)
    if len(exist) == 0:
        lines.append(f'export JAVA_HOME={java_home}\n')

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
        remote_path = os.path.join(directory, 'hive-env.sh')
        with sftp.file(remote_path, 'w') as remote_file:
            remote_file.write(''.join(lines))  # Concatenate lines into a single string

        print(f"File saved to {remote_host}:{remote_path}")
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        sftp.close()
        ssh_client.close()

def update_hive_site(hostname, directory):
    with open(config['general']['hadoop_cluster']+config['hive']['conf_path']+'hive-site.xml', 'r') as file:
        lines = file.readlines()

    zookeeper_nodes = [f'{h}:2181' for h in hostnames.keys()]
    zookeeper_string = ','.join(zookeeper_nodes)

    replace_dict = {
        '<name>hive.metastore.uris</name>': f'     <value>thrift://{list(hostnames)[0]}:9083</value>\n',
        '<name>javax.jdo.option.ConnectionURL</name>': f'     <value>jdbc:mysql://{list(hostnames)[0]}:3306/{database}?useSSL=false</value>\n',
        '<name>javax.jdo.option.ConnectionDriverName</name>': f'     <value>com.mysql.cj.jdbc.Driver</value>\n',
        '<name>javax.jdo.option.ConnectionUserName</name>': f'     <value>{username}</value>\n',
        '<name>javax.jdo.option.ConnectionPassword</name>': f'     <value>{password}</value>\n',
        '<name>hive.security.authorization.enabled</name>': f'     <value>true</value>\n',
        '<name>hive.security.authorization.manager</name>': f'     <value>org.apache.ranger.authorization.hive.authorizer.RangerHiveAuthorizerFactory</value>\n',
        '<name>hive.security.authenticator.manager</name>': f'     <value>org.apache.hadoop.hive.ql.security.SessionStateUserAuthenticator</value>\n',
        '<name>hive.metastore.event.db.notification.api.auth</name>': f'     <value>false</value>\n',
        '<name>hive.server2.thrift.bind.host</name>': f'     <value>{list(hostnames)[0]}</value>\n',
        '<name>hive.zookeeper.quorum</name>': f'     <value>{zookeeper_string}</value>\n'
    }

    for i, line in enumerate(lines):
        for key, value in replace_dict.items():
            if key in line:
                if callable(value):
                    lines[i+1] = value(line)
                else:
                    lines[i+1] = value
                break
    if "master" in hostname:
        lines_to_append = """
    <property>
        <name>ranger.plugin.hive.service.name</name>
        <value>HIVE</value>
    </property>
    <property>
        <name>ranger.plugin.hive.policy.pollIntervalMs</name>
        <value>600</value>
    </property>
    <property>
        <name>ranger.plugin.hive.enable</name>
        <value>true</value>
    </property>
</configuration>
        """
        filtered_lines = [line for line in lines if '</configuration>' not in line]
        filtered_lines.append(lines_to_append)
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
        remote_path = os.path.join(directory, 'hive-site.xml')
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
    directory = config['general']['hadoop_cluster']+config['hive']['conf_path']
    update_hive_env(java_home, directory)
    update_hive_site(hostname, directory)
import paramiko
import time
import yaml

yaml_file_path = "/usr/local/Big-Data-Platform/Infra/environmentvariables.yaml"
with open(yaml_file_path, 'r') as yaml_file:
    config = yaml.safe_load(yaml_file)

number_of_nodes= config['general']['number_of_nodes']
system_username = config['ssh']['remote_username']
# Define an array of remote hosts
remote_hosts = [
    (system_username, "master-public", f"/home/{system_username}/.ssh/id_rsa")
]
for i in range(2,number_of_nodes+1):
    remote_hosts.append((system_username, f"worker-public{i-1}", f"/home/{system_username}/.ssh/id_rsa"))
    # Add more hosts here as needed

# Lines to append to the .bashrc file
lines_to_append = [
    'export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64',
    'export PATH=$JAVA_HOME/bin:$PATH',
    'export HADOOP_HOME=/usr/local/hadoopcluster/hadoop-3.3.5',
    'export PATH=$PATH:$HADOOP_HOME/bin',
    'export PATH=$PATH:$HADOOP_HOME/sbin',
    'export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop',
    'export HADOOP_MAPRED_HOME=$HADOOP_HOME',
    'export HADOOP_COMMON_HOME=$HADOOP_HOME',
    'export HADOOP_HDFS_HOME=$HADOOP_HOME',
    'export YARN_HOME=$HADOOP_HOME',
    'export KAFKA_HOME=/usr/local/hadoopcluster/kafka_2.12-3.4.0',
    'export PATH=$PATH:$KAFKA_HOME/bin',
    'export HIVE_HOME=/usr/local/hadoopcluster/apache-hive-3.1.3-bin',
    'export PATH=$PATH:$HIVE_HOME/bin',
    'export NIFI_HOME=/usr/local/hadoopcluster/nifi-1.22.0',
    'export PATH=$PATH:$NIFI_HOME/bin',
    'export SPARK_HOME=/usr/local/hadoopcluster/spark-3.4.1-bin-hadoop3',
    'export PATH=$PATH:$SPARK_HOME/sbin',
    'export PATH=$PATH:~/.local/bin',
    'export AIRFLOW_HOME=/usr/local/airflow'
    'alias jphs="/usr/local/Big-Data-Platform/Infra/bash_files/hadoop_pid.sh"',
    'alias ssh_key="~/.ssh/id_rsa"'
]

# Loop through the remote hosts and append lines to .bashrc
for user, host, key_file in remote_hosts:
    # Create an SSH client instance
    ssh = paramiko.SSHClient()
    
    # Automatically add the remote host's key (make sure it's secure in a production environment)
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print(host, user, key_file)
        # Load the PEM file for authentication
        ssh.connect(host, username=user, key_filename=key_file)
        
        # Read the current .bashrc content
        stdin, stdout, stderr = ssh.exec_command("cat ~/.bashrc")
        current_content = stdout.read().decode('utf-8')
        
        # Remove lines after line 118
        current_lines = current_content.split('\n')
        new_content = '\n'.join(current_lines[:118])
        
        # Append the new lines
        new_content += '\n' + '\n'.join(lines_to_append)
        
        # Write the modified content to .bashrc
        with ssh.open_sftp().file('/tmp/bashrc_tmp', 'w') as tmp_file:
            tmp_file.write(new_content)
        
        # Overwrite the .bashrc with the modified content
        ssh.exec_command("cat /tmp/bashrc_tmp > ~/.bashrc && source ~/.bashrc")

        print(f'Successfully updated .bashrc on {host}')
    except Exception as e:
        print(f'Error updating .bashrc on {host}: {str(e)}')
    finally:
        # Close the SSH connection
        ssh.close()
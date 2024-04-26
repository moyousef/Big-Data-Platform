import os
import paramiko
import xml.dom.minidom as minidom
import yaml

yaml_file_path = "/usr/local/Big-Data-Platform/Infra/environmentvariables.yaml"

with open(yaml_file_path, 'r') as yaml_file:
    config = yaml.safe_load(yaml_file)

# Create a list of hostnames and corresponding directories
hostnames = config['hostnames']
system_username = config['ssh']['remote_username']
hosturls = config['hosturls']
xml_str_full = {}
exist = []
java_home = config['java']['home']
pid = config['hadoop']['pid_path']
hadoop_cluster = config['general']['hadoop_cluster']

number_of_nodes= config['general']['number_of_nodes']
def update_hadoop_env(pid, java_home, directory):
    with open(config['general']['hadoop_cluster']+config['hadoop']['conf_path']+'hadoop-env.sh', 'r') as file:
        lines = file.readlines()

    filtered_lines = [line for line in lines if 'export HADOOP_PID_DIR' not in line and 'export JAVA_HOME' not in line]
    if number_of_nodes > 1 :
        filtered_lines.append(f'export JAVA_HOME={java_home}\n')
        filtered_lines.append(f'export HADOOP_PID_DIR={pid}\n')

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
        remote_path = os.path.join(directory, 'hadoop-env.sh')
        with sftp.file(remote_path, 'w') as remote_file:
            remote_file.write(''.join(lines))  # Concatenate lines into a single string

        print(f"File saved to {remote_host}:{remote_path}")
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        sftp.close()
        ssh_client.close()

def create_core_site_str(xml_str_full):

    # Define the values to be written to the core-site.xml file
    core_site_values = {
        "fs.defaultFS": "hdfs://master-node:9000",
        f"hadoop.proxyuser.{system_username}.hosts": "*",
        f"hadoop.proxyuser.{system_username}.groups": "*"
    }

    # Create the root element for the XML
    root = minidom.Document()
    config = root.createElement("configuration")
    root.appendChild(config)

    # Add properties to the XML with proper indentation
    for key, value in core_site_values.items():
        prop = root.createElement("property")
        name = root.createElement("name")
        name.appendChild(root.createTextNode(key))
        value_elem = root.createElement("value")
        value_elem.appendChild(root.createTextNode(value))
        prop.appendChild(name)
        prop.appendChild(value_elem)
        config.appendChild(prop)
        config.appendChild(root.createTextNode('\n  '))  # Add a newline and two spaces

    # Serialize the XML with indentation
    xml_str = root.toprettyxml(indent="  ")
    xml_str_full["core-site.xml"] = xml_str
    return xml_str_full

def create_hdfs_site_master_str(xml_str_full):
    # Define the values to be written to the hdfs-site.xml file
    hdfs_site_values = {
        "dfs.replication": "3",
        "dfs.namenode.name.dir": f"{hadoop_cluster}/hdfs/data/namenode",
        "dfs.datanode.data.dir": f"{hadoop_cluster}/hdfs/data/datanode"
    }

    # Create the root element for the XML
    root = minidom.Document()
    config = root.createElement("configuration")
    root.appendChild(config)

    # Add properties to the XML with proper indentation
    for key, value in hdfs_site_values.items():
        prop = root.createElement("property")
        name = root.createElement("name")
        name.appendChild(root.createTextNode(key))
        value_elem = root.createElement("value")
        value_elem.appendChild(root.createTextNode(value))
        prop.appendChild(name)
        prop.appendChild(value_elem)
        config.appendChild(prop)
        config.appendChild(root.createTextNode('\n  '))  # Add a newline and two spaces

    # Serialize the XML with indentation
    xml_str = root.toprettyxml(indent="  ")
    xml_str_full["masterhdfs-site.xml"] = xml_str
    return xml_str_full

def create_hdfs_site_worker_str(xml_str_full):
    hdfs_site_values = {
        "dfs.datanode.data.dir": f"{hadoop_cluster}/hdfs/data/datanode",
        "dfs.datanode.address": "0.0.0.0:50010",
        "dfs.datanode.http.address": "0.0.0.0:50075",
        "dfs.datanode.https.address": "0.0.0.0:50475",
        "dfs.datanode.ipc.address": "0.0.0.0:8010"
    }

    # Create the root element for the XML
    root = minidom.Document()
    config = root.createElement("configuration")
    root.appendChild(config)

    # Add properties to the XML with proper indentation
    for key, value in hdfs_site_values.items():
        prop = root.createElement("property")
        name = root.createElement("name")
        name.appendChild(root.createTextNode(key))
        value_elem = root.createElement("value")
        value_elem.appendChild(root.createTextNode(value))
        prop.appendChild(name)
        prop.appendChild(value_elem)
        config.appendChild(prop)
        config.appendChild(root.createTextNode('\n  '))  # Add a newline and two spaces

    # Serialize the XML with indentation
    xml_str = root.toprettyxml(indent="  ")
    xml_str_full["slavehdfs-site.xml"] = xml_str
    return xml_str_full

def create_hdfs_yarn_master_str(xml_str_full):
    hdfs_site_values = {
        "yarn.resourcemanager.hostname": "master-node",
        "yarn.resourcemanager.address": "master-node:8032",
        "yarn.resourcemanager.resource-tracker.address": "master-node:8031",
        "yarn.resourcemanager.scheduler.address": "master-node:8030",
        "yarn.resourcemanager.webapp.address": "master-node:8088",
        "yarn.resourcemanager.webapp.https.address": "master-node:8090",
    }

    yarn_site = "yarn-site.xml"

    # Create the root element for the XML
    root = minidom.Document()
    config = root.createElement("configuration")
    root.appendChild(config)

    # Add properties to the XML with proper indentation
    for key, value in hdfs_site_values.items():
        prop = root.createElement("property")
        name = root.createElement("name")
        name.appendChild(root.createTextNode(key))
        value_elem = root.createElement("value")
        value_elem.appendChild(root.createTextNode(value))
        prop.appendChild(name)
        prop.appendChild(value_elem)
        config.appendChild(prop)
        config.appendChild(root.createTextNode('\n  '))  # Add a newline and two spaces

    # Serialize the XML with indentation
    xml_str = root.toprettyxml(indent="  ")
    xml_str_full["masteryarn-site.xml"] = xml_str
    return xml_str_full

def create_hdfs_yarn_worker_str(xml_str_full):
    hdfs_site_values = {
        "yarn.nodemanager.local-dirs": f"/home/{system_username}/hadoop/yarn/local",
        "yarn.nodemanager.log-dirs": f"/home/{system_username}/hadoop/yarn/logs",
    }

    yarn_site = "yarn-site.xml"

    # Create the root element for the XML
    root = minidom.Document()
    config = root.createElement("configuration")
    root.appendChild(config)

    # Add properties to the XML with proper indentation
    for key, value in hdfs_site_values.items():
        prop = root.createElement("property")
        name = root.createElement("name")
        name.appendChild(root.createTextNode(key))
        value_elem = root.createElement("value")
        value_elem.appendChild(root.createTextNode(value))
        prop.appendChild(name)
        prop.appendChild(value_elem)
        config.appendChild(prop)
        config.appendChild(root.createTextNode('\n  '))  # Add a newline and two spaces

    # Serialize the XML with indentation
    xml_str = root.toprettyxml(indent="  ")
    xml_str_full["slaveyarn-site.xml"] = xml_str
    return xml_str_full

def update_all_hadoop(xml_str_full, directory):
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
        for filename, xml_str in xml_str_full.items():
            if "master" in filename and hostname == "master-node":
                filename = filename.split('master')[1]
            elif "slave" in filename and hostname != "master-node":
                filename = filename.split('slave')[1]
            remote_path = os.path.join(directory, filename)

            with sftp.file(remote_path, "w") as file:
                file.write(xml_str)

            print(f"{filename} updated at {remote_host}:{remote_path}")

    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        sftp.close()
        ssh_client.close()


xml_str_full = create_core_site_str(xml_str_full)
xml_str_full = create_hdfs_site_master_str(xml_str_full)
xml_str_full = create_hdfs_site_worker_str(xml_str_full)
xml_str_full = create_hdfs_yarn_master_str(xml_str_full)
xml_str_full = create_hdfs_yarn_worker_str(xml_str_full)

for hostname, directory in hostnames.items():
    directory = config['general']['hadoop_cluster']+config['hadoop']['conf_path']
    update_hadoop_env(pid, java_home, directory)
    update_all_hadoop(xml_str_full, directory)

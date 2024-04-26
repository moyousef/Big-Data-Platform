import os
import yaml
import paramiko

# Load environment variables from environmentvariables.yaml
config_file_path = "/usr/local/Big-Data-Platform/Infra/environmentvariables.yaml"
with open(config_file_path, "r") as env_file:
    env_vars = yaml.safe_load(env_file)

# Get Spark configuration details from environment variables
hostnames = env_vars["hosturls"]
master = env_vars["hosturls"]["master-node"]
system_username = env_vars['ssh']['remote_username']

def spark(master, hosturl, directory):
    # Set Spark configuration for master
    spark_master_config = {
        "spark.master": f"spark://{master}:7077",
    }

    # Create directories if they don't exist
    os.makedirs(os.path.join(directory, "conf"), exist_ok=True)

    # Write Spark configuration for worker
    with open(os.path.join(directory, "conf", "spark-defaults.conf"), "w") as worker_config_file:
        for key, value in spark_master_config.items():
            worker_config_file.write(f"{key} {value}\n")

    # Now, connect to the worker node and update its spark-defaults.conf
    try:
        ssh_client = paramiko.SSHClient()
        ssh_client.load_system_host_keys()
        ssh_client.connect(hosturl)
        sftp_client = ssh_client.open_sftp()

        # Update spark-defaults.conf on the worker node
        remote_spark_defaults_path = os.path.join(directory, "conf", "spark-defaults.conf")
        sftp_client.put(os.path.join(directory, "conf", "spark-defaults.conf"), remote_spark_defaults_path)
        sftp_client.close()
        ssh_client.close()
        print("Configuration updated on the worker node.")

    except Exception as e:
        print(f"Failed to update configuration on worker node: {e}")

    print("Spark configuration for master and worker nodes completed.")

for hostname, hosturl in hostnames.items():
    directory = env_vars['general']['hadoop_cluster']+env_vars['spark']['spark_path']
    spark(master,hosturl,directory)
    
    if "master" in hosturl:
        # Set the Spark master host in spark-env.sh for the worker
        with open(os.path.join(directory, "conf", "spark-env.sh"), "w") as spark_env_file:
            spark_env_file.write(f'export SPARK_MASTER_HOST={hosturl}')
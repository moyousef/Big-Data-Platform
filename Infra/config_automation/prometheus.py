import yaml
import paramiko

# Load environment variables from environmentvariables.yaml
with open("/usr/local/Big-Data-Platform/Infra/environmentvariables.yaml", "r") as env_file:
    env_vars = yaml.safe_load(env_file)

system_username = env_vars['ssh']['remote_username']
prometheus_directory = env_vars['general']['hadoop_cluster']+env_vars['prometheus']['prom_path']
node_exporter_path = env_vars['general']['hadoop_cluster']+env_vars['prometheus']['node_exporter_path']

def start_node_exporter(host, private_key_path):
    try:
        ssh_client = paramiko.SSHClient()
        ssh_client.load_system_host_keys()
        ssh_client.connect(host, username=env_vars["ssh"]["remote_username"], key_filename=private_key_path)

        # Create node_exporter.yml with the necessary configuration
        node_exporter_config = 'web.listen-address=:9100\n'
        node_exporter_config_file = 'node_exporter.yml'
        with ssh_client.open_sftp().file(node_exporter_path + node_exporter_config_file, 'w') as config_file:
            config_file.write(node_exporter_config)

        # Start Node Exporter
        #start_command = f'{node_exporter_path}/node_exporter --config.file=node_exporter.yml &'
        #stdin, stdout, stderr = ssh_client.exec_command(start_command)

        print(f"Node Exporter configure on {host}")

    except Exception as e:
        print(f"Failed to configure Node Exporter on {host}: {e}")

    finally:
        ssh_client.close()

# Define the Prometheus configuration
prometheus_config = {
    "global": {
        "scrape_interval": "15s",
        "evaluation_interval": "15s",
        "scrape_timeout": "10s",
    },
    "alerting": {
        "alertmanagers": [{"static_configs": [{"targets": ["alertmanager:9093"]}]}
        ],
    },
    "rule_files": ["alert.rules.yml"],
    "scrape_configs": [],
}

# Add a scrape job for the master node and start Node Exporter
scrape_job_master = {
    "job_name": "node_exporter_master",
    "static_configs": [
        {
            "targets": [env_vars["hosturls"]["master-node"] + ":9100"]
        }
    ],
    "scrape_interval": "15s",
}
prometheus_config["scrape_configs"].append(scrape_job_master)
start_node_exporter(env_vars["hosturls"]["master-node"], env_vars["ssh"]["private_key_path"])

# Add scrape jobs for worker nodes and start Node Exporter
for hostname, ip in env_vars["hosturls"].items():
    if hostname != "master-node":
        scrape_job_worker = {
            "job_name": f"node_exporter_{hostname}",
            "static_configs": [
                {
                    "targets": [ip + ":9100"]
                }
            ],
            "scrape_interval": "15s",
        }
        prometheus_config["scrape_configs"].append(scrape_job_worker)
        start_node_exporter(ip, env_vars["ssh"]["private_key_path"])

# Define alerting rules as a list
alert_rules = [
    {
        "alert": "HighCPULoad",
        "expr": '100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80',
        "for": "5m",
        "labels": {
            "severity": "warning",
        },
        "annotations": {
            "summary": "High CPU Usage Detected",
            "description": "The average CPU usage is above 80% for 5 minutes.",
        },
    },
    {
        "alert": "HighRAMUsage",
        "expr": '(1 - (node_memory_MemFree_bytes / node_memory_MemTotal_bytes)) * 100 > 80',
        "for": "5m",
        "labels": {
            "severity": "warning",
        },
        "annotations": {
            "summary": "High RAM Usage Detected",
            "description": "The RAM usage is above 80% for 5 minutes.",
        },
    },
    {
        "alert": "HighDiskUsage",
        "expr": 'node_filesystem_avail_bytes{mountpoint="/",fstype!="rootfs"} / node_filesystem_size_bytes{mountpoint="/",fstype!="rootfs"} * 100 < 20',
        "for": "5m",
        "labels": {
            "severity": "warning",
        },
        "annotations": {
            "summary": "High Disk Usage Detected",
            "description": "The disk usage is below 20% free space for 5 minutes.",
        },
    },
]

# Create or overwrite the Prometheus configuration YAML file (prometheus.yml)
with open(prometheus_directory + "prometheus.yml", "w") as prometheus_config_file:
    yaml.dump(prometheus_config, prometheus_config_file, default_flow_style=False)

# Create or overwrite the alerting rules YAML file (alert_rules.yml)
with open(prometheus_directory + "alert_rules.yml", "w") as alert_rules_file:
    yaml.dump(alert_rules, alert_rules_file, default_flow_style=False)

import configparser
import yaml
import sys

yaml_file_path = "/usr/local/Big-Data-Platform/Infra/environmentvariables.yaml"

with open(yaml_file_path, 'r') as yaml_file:
    yaml_config = yaml.safe_load(yaml_file)

system_username = yaml_config['ssh']['remote_username']

# Read the INI file
config = configparser.ConfigParser(allow_no_value=True)
config.optionxform = str  # Preserve case sensitivity
config.read(f'/usr/local/Big-Data-Platform/Infra/inventory.ini')
existing_machines = config['Existing_Machines']
hostnames = sys.argv[1:]

# Delete the line containing 'worker-public2'
for key, value in existing_machines.items():
    for hostname in hostnames:
        node = hostname.split("public")[1]
        hostnode = (f"slave-node{node}")
        if hostname in key:
            config.remove_option('Existing_Machines', hostname+" ansible_ssh_host")
            del yaml_config['hostnames'][hostnode]
            del yaml_config['hosturls'][hostnode]
            yaml_config['general']['number_of_nodes'] = yaml_config['general']['number_of_nodes'] - 1
        else:
            print("none", key)

with open(yaml_file_path, 'w') as env_file:
    yaml.dump(yaml_config, env_file)

# Write the updated content back to the INI file with white spaces removed around the equal sign
with open(f'/usr/local/Big-Data-Platform/Infra/inventory.ini', 'w') as configfile:
    for section in config.sections():
        configfile.write(f"[{section}]\n")
        for key, value in config.items(section):
            configfile.write(f"{key.strip()}={value.strip()}\n")
        configfile.write("\n")

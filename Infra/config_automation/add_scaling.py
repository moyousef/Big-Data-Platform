import configparser
import yaml
import sys

yaml_file_path = "/usr/local/Big-Data-Platform/Infra/environmentvariables.yaml"

with open(yaml_file_path, 'r') as yaml_file:
    env_config = yaml.safe_load(yaml_file)

hostnames = sys.argv[1:]
system_username = env_config['ssh']['remote_username']

# Read the INI file
config = configparser.ConfigParser(allow_no_value=True)
config.optionxform = str  # Preserve case sensitivity
config.read(f'/usr/local/Big-Data-Platform/Infra/inventory.ini')

for hostname in hostnames:
    node = hostname.split("public")[1]
    hostnode = (f"slave-node{node}")
    env_config['hostnames'][hostnode] = ""
    env_config['hosturls'][hostnode] = hostname

    # Add a custom string to the [Scaling] group
    config.set('Scaling', f'{hostname} ansible_ssh_host', f'{hostname} ansible_ssh_private_key_file=~/.ssh/id_rsa ansible_ssh_common_args="-o StrictHostKeyChecking=no"')

    # Write the updated content back to the INI file with white spaces removed around the equal sign
    with open(f'/usr/local/Big-Data-Platform/Infra/inventory.ini', 'w') as configfile:
        for section in config.sections():
            configfile.write(f"[{section}]\n")
            for key, value in config.items(section):
                configfile.write(f"{key.strip()}={value.strip()}\n")
            configfile.write("\n")

env_config['general']['number_of_nodes'] = int(hostnames[-1].split("public")[1]) + 1
with open(yaml_file_path, 'w') as env_file:
    yaml.dump(env_config, env_file)
import configparser
import yaml

yaml_file_path = "/usr/local/Big-Data-Platform/Infra/environmentvariables.yaml"

with open(yaml_file_path, 'r') as yaml_file:
    yaml_config = yaml.safe_load(yaml_file)

system_username = yaml_config['ssh']['remote_username']

# Read the INI file
config = configparser.ConfigParser(allow_no_value=True)
config.optionxform = str  # Preserve case sensitivity
config.read(f'/usr/local/Big-Data-Platform/Infra/inventory.ini')

# Get the parameters from the [Scaling] group
scaling_parameters = config.items('Scaling')

# Move the parameters to the [Existing_Machines] group
for key, value in scaling_parameters:
    config.set('Existing_Machines', key, value)

# Clear the [Scaling] section
if 'Scaling' in config:
    for key in config.options('Scaling'):
        config.remove_option('Scaling', key)

# Write the updated content back to the INI file with white spaces removed around the equal sign
with open(f'/usr/local/Big-Data-Platform/Infra/inventory.ini', 'w') as configfile:
    for section in config.sections():
        configfile.write(f"[{section}]\n")
        for key, value in config.items(section):
            configfile.write(f"{key.strip()}={value.strip()}\n")
        configfile.write("\n")

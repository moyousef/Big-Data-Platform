#!/bin/bash

source credentials.env
# Function to parse worker IPs from the .env file
parse_workers_ips() {
    while IFS= read -r line; do
        if [[ "$line" =~ ^workers_ips= ]]; then
            ips_str=$(echo "$line" | cut -d'=' -f2 | tr -d '()"' | xargs)
            echo $ips_str
            return
        fi
    done < "$1"
}

# Main function to generate inventory from .env file
generate_inventory_from_env() {
    env_file_path=$1
    inventory_file_path=$2

    # Call function to parse IPs
    workers_ips=$(parse_workers_ips "$env_file_path")

    # Define static part of the inventory
    inventory_content="[Scaling]\n"
    master_line="master-public ansible_ssh_host=master-public ansible_ssh_private_key_file=~/.ssh/id_rsa ansible_ssh_common_args='-o StrictHostKeyChecking=no'\n"
    inventory_content+="$master_line"

    # Loop over worker IPs
    i=1
    for ip in $workers_ips; do
        worker_name="worker-public$i"
        inventory_content+="${worker_name} ansible_ssh_host=${worker_name} ansible_ssh_private_key_file=~/.ssh/id_rsa ansible_ssh_common_args='-o StrictHostKeyChecking=no'\n"
        ((i++))
    done

    inventory_content+="\n[Existing_Machines]\n\n[Master_Node]\n$master_line\n[all:vars]\n"

    # Append .env variables to the inventory content
    while IFS= read -r line; do
        inventory_content+="$line\n"
    done < "$env_file_path"

    # Write to the inventory file
    echo -e "$inventory_content" > "$inventory_file_path"
}

env_file_path="$credentials_file_path/credentials.env"
inventory_file_path="$inventory_file_path/inventory.ini"

generate_inventory_from_env "$env_file_path" "$inventory_file_path"

import os
import paramiko
import yaml

yaml_file_path = "/usr/local/Big-Data-Platform/Infra/environmentvariables.yaml"

with open(yaml_file_path, 'r') as yaml_file:
    config = yaml.safe_load(yaml_file)

hostnames = config['hostnames']
hosturls = config['hosturls']
hadoop_conf = config['general']['hadoop_cluster']+config['hadoop']['conf_path']
hadoop_home = hadoop_conf.split("/etc")[0]
hive_conf = config['general']['hadoop_cluster']+config['hive']['conf_path']
hive_home = hadoop_conf.split("/conf")[0]
number_of_nodes= config['general']['number_of_nodes']
username = config['ssh']['remote_username']
group = config['ssh']['group']
passw = config['ssh']['pass']
admin_pass = config['ranger']['admin_pass']
binddn = config['ranger']['binddn']
bindpass = config['ranger']['bindpass']
search_base = config['ranger']['search_base']
user_search_base = config['ranger']['user_search_base']
group_search_base = config['ranger']['group_search_base']
search_scope = config['ranger']['search_scope']
mysql_root_password = config['ranger']['mysql_root_password']
db_user = config['ranger']['db_user']

def update_admin_install(hostname, directory, hadoop_conf):

    with open(config['general']['hadoop_cluster']+config['ranger']['ranger_admin']+'install.properties', 'r') as file:
        lines = file.readlines()

    replace_dict = {
        'db_root_password=': f'db_root_password={mysql_root_password}\n',
        'db_host=': f'db_host={hostname}:3306\n',
        'db_user=': f'db_user={db_user}\n',
        'db_password': f'db_password={mysql_root_password}\n',
        'rangerAdmin_password=': f'rangerAdmin_password={admin_pass}\n',
        'rangerTagsync_password=': f'rangerTagsync_password={admin_pass}\n',
        'rangerUsersync_password=': f'rangerUsersync_password={admin_pass}\n',
        'keyadmin_password=': f'keyadmin_password={admin_pass}\n',
        'audit_elasticsearch_urls=': f'audit_elasticsearch_urls={hostname}\n',
        'audit_solr_urls=': f'audit_solr_urls=http://{hostname}:6083/solr/ranger_audits\n',
        'audit_solr_user=': f'audit_solr_user={db_user}\n',
        'audit_solr_password=': f'audit_solr_password={admin_pass}\n',
        'policymgr_external_url=': f'policymgr_external_url=http://{hostname}:6080\n',
        'unix_user=': f'unix_user={username}\n',
        'unix_user_pwd=': f'unix_user_pwd={passw}\n',
        'unix_group=': f'unix_group={group}\n',
        'authentication_method=': 'authentication_method=NONE\n',
        'hadoop_conf=': f'hadoop_conf={hadoop_conf}\n',
        'sso_providerurl=': f'sso_providerurl=https://{hostname}:8443/gateway/knoxsso/api/v1/websso\n'
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
        remote_path = os.path.join(directory, 'install.properties')
        with sftp.file(remote_path, 'w') as remote_file:
            remote_file.write(''.join(lines))  # Concatenate lines into a single string

        print(f"File saved to {remote_host}:{remote_path}")
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        sftp.close()
        ssh_client.close()

def update_hdfs_install(hostname, directory,hadoop_home):
    with open(config['general']['hadoop_cluster']+config['ranger']['ranger_hdfs']+'install.properties', 'r') as file:
        lines = file.readlines()

    for i, line in enumerate(lines):
        if line.startswith("POLICY_MGR_URL="):
            lines[i] = f'POLICY_MGR_URL=http://{hostname}:6080\n'
        elif line.startswith("COMPONENT_INSTALL_DIR_NAME="):
            lines[i] = f'COMPONENT_INSTALL_DIR_NAME={hadoop_home}\n'
        elif line.startswith("COMPONENT_INSTALL_DIR_NAME=CUSTOM_USER="):
            lines[i] = f'CUSTOM_USER={username}\n'
        elif line.startswith("CUSTOM_GROUP="):
            lines[i] = f'CUSTOM_GROUP={group}\n'

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
        remote_path = os.path.join(directory, 'install.properties')
        with sftp.file(remote_path, 'w') as remote_file:
            remote_file.write(''.join(lines))  # Concatenate lines into a single string

        print(f"File saved to {remote_host}:{remote_path}")
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        sftp.close()
        ssh_client.close()

def update_usersync_install(hostname, directory,hadoop_home):
    with open(config['general']['hadoop_cluster']+config['ranger']['ranger_usersync']+'install.properties', 'r') as file:
        lines = file.readlines()

    replace_dict = {
        'ranger_base_dir =': f'ranger_base_dir = {directory}\n',
        'POLICY_MGR_URL =': f'POLICY_MGR_URL = http://{hostname}:6080/\n',
        'SYNC_SOURCE': 'SYNC_SOURCE = ldap\n',
        'SYNC_INTERVAL =': 'SYNC_INTERVAL = 1\n',
        'unix_user=': f'unix_user={username}\n',
        'unix_group=': f'unix_group={group}\n',
        'rangerUsersync_password=': f'rangerUsersync_password={admin_pass}\n',
        'hadoop_conf=': f'hadoop_conf={hadoop_conf}\n',
        'SYNC_LDAP_URL =': f'SYNC_LDAP_URL = ldap://{hostname}:389\n',
        'SYNC_LDAP_BIND_DN': f'SYNC_LDAP_BIND_DN = {binddn}\n',
        'SYNC_LDAP_BIND_PASSWORD': f'SYNC_LDAP_BIND_PASSWORD = {bindpass}\n',
        'SYNC_LDAP_SEARCH_BASE = ': f'SYNC_LDAP_SEARCH_BASE = {search_base}\n',
        'SYNC_LDAP_USER_SEARCH_BASE = ': f'SYNC_LDAP_USER_SEARCH_BASE = {user_search_base}\n',
        'SYNC_LDAP_USER_SEARCH_SCOPE = ': f'SYNC_LDAP_USER_SEARCH_SCOPE = {search_scope}\n',
        'SYNC_LDAP_USER_SEARCH_FILTER = ': '(objectClass=*)\n',
        'SYNC_LDAP_USER_NAME_ATTRIBUTE =': 'SYNC_LDAP_USER_NAME_ATTRIBUTE = uid\n',
        'SYNC_GROUP_SEARCH_ENABLED=': 'SYNC_GROUP_SEARCH_ENABLED=true\n',
        'SYNC_GROUP_USER_MAP_SYNC_ENABLED=': 'SYNC_GROUP_USER_MAP_SYNC_ENABLED=true\n',
        'SYNC_GROUP_SEARCH_BASE=': f'SYNC_GROUP_SEARCH_BASE={group_search_base}\n',
        'SYNC_GROUP_SEARCH_SCOPE=': 'SYNC_GROUP_SEARCH_SCOPE=sub\n',
        'SYNC_GROUP_OBJECT_CLASS=': 'SYNC_GROUP_OBJECT_CLASS=posixGroup\n',
        'SYNC_LDAP_GROUP_SEARCH_FILTER=': 'SYNC_LDAP_GROUP_SEARCH_FILTER=(objectClass=*)\n',
        'SYNC_GROUP_NAME_ATTRIBUTE=': 'SYNC_GROUP_NAME_ATTRIBUTE=uid\n'
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
        remote_path = os.path.join(directory, 'install.properties')
        with sftp.file(remote_path, 'w') as remote_file:
            remote_file.write(''.join(lines))  # Concatenate lines into a single string

        print(f"File saved to {remote_host}:{remote_path}")
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        sftp.close()
        ssh_client.close()

def update_hive_install(hostname, directory,hive_home):
    with open(config['general']['hadoop_cluster']+config['ranger']['ranger_hive']+'install.properties', 'r') as file:
        lines = file.readlines()

    for i, line in enumerate(lines):
        if line.startswith("POLICY_MGR_URL="):
            lines[i] = f'POLICY_MGR_URL=http://{hostname}:6080\n'
        elif line.startswith("COMPONENT_INSTALL_DIR_NAME="):
            lines[i] = f'COMPONENT_INSTALL_DIR_NAME={hive_home}\n'
        elif line.startswith("COMPONENT_INSTALL_DIR_NAME=CUSTOM_USER="):
            lines[i] = f'CUSTOM_USER={username}\n'
        elif line.startswith("CUSTOM_GROUP="):
            lines[i] = f'CUSTOM_GROUP={group}\n'

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
        remote_path = os.path.join(directory, 'install.properties')
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
        directory = config['general']['hadoop_cluster']+config['ranger']['ranger_admin']
        update_admin_install(hostname, directory,hadoop_conf)
        directory = config['general']['hadoop_cluster']+config['ranger']['ranger_hdfs']
        update_hdfs_install(hostname, directory,hadoop_home)
        directory = config['general']['hadoop_cluster']+config['ranger']['ranger_usersync']
        update_usersync_install(hostname, directory,hadoop_home)
        directory = config['general']['hadoop_cluster']+config['ranger']['ranger_hive']
        update_hive_install(hostname, directory,hive_home)
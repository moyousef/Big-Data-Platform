from flask import Flask, request, jsonify
import subprocess
import re
import yaml
import os

yaml_file_path = "/home/wakeb/Big-Data-Platform/Infra/API/environmentvariables.yaml"

with open(yaml_file_path, 'r') as yaml_file:
    config = yaml.safe_load(yaml_file)

binddn = config['ldap']['binddn']
domain = config['ldap']['domain']
user_search_base = config['ldap']['user_search_base']
group_search_base = config['ldap']['group_search_base']
uri = config['ldap']['URI']

app = Flask(__name__)

@app.route('/create_user', methods=['GET'])
def create_user():
    username = request.args.get('user')
    group = request.args.get('group')
    user_org = request.args.get('user_org')
    group_org = request.args.get('group_org')
    password = request.args.get('password')
    ldap_password = request.args.get('ldap_password')

    if not username:
        return 'Please provide a username.', 400
    if not password:
        return 'Please provide a password.', 400
    if not ldap_password:
        return 'Please provide a password for ldap.', 400
    user_base = user_search_base    
    if user_org:
        user_base = f'ou={user_org},{domain}'   
    group_base = group_search_base    
    if group_org:
        group_base = f'ou={group_org},{domain}'  
    try:    
        uid_number = get_next_available_uid()
        gid_number = get_available_group_gid(group, group_base)
        password_hash = generate_ssha_password(password)
        ldif_content = generate_ldif_user(username, uid_number, group, gid_number, password_hash, user_base, group_base)
        file_path = f'{username}.ldif'
        with open(file_path, 'w') as f:
            f.write(ldif_content)
        
        run_ldif(file_path,ldap_password)
        return f'User {username} created successfully.'
    except Exception as e:
        return f'Error creating user: {str(e)}', 500

@app.route('/create_group', methods=['GET'])
def create_group():
    group = request.args.get('group')
    org = request.args.get('org')
    ldap_password = request.args.get('ldap_password')
    if not group:
        return 'Please provide a group name.', 400
    if not ldap_password:
        return 'Please provide a password for ldap.', 400
    group_base = group_search_base    
    if org:
        group_base = f'ou={org},{domain}'
    try:
        gid_number = get_next_available_gid()    
        ldif_content = generate_ldif_group(group, gid_number, group_base)
        file_path = f'{group}.ldif'
        with open(file_path, 'w') as f:
            f.write(ldif_content)
        
        run_ldif(file_path,ldap_password)
        return f'Group {group} created successfully.'
    except Exception as e:
        return f'Error creating group: {str(e)}', 500

@app.route('/create_org', methods=['GET'])
def create_org():
    org = request.args.get('org')
    ldap_password = request.args.get('ldap_password')
    if not org:
        return 'Please provide a org name.', 400
    if not ldap_password:
        return 'Please provide a password for ldap.', 400    
    try:
        ldif_content = generate_ldif_org(org)
        file_path = f'{org}.ldif'
        with open(file_path, 'w') as f:
            f.write(ldif_content)
        
        run_ldif(file_path,ldap_password)
        return f'Organization {org} created successfully.'
    except Exception as e:
        return f'Error creating organization: {str(e)}', 500
    
@app.route('/search', methods=['GET'])
def search():
    user = request.args.get('user')
    group = request.args.get('group')
    org = request.args.get('org')
    search_attribute = request.args.get('search_attribute')
    if user and org:
        search_dn = f'uid={user},ou={org},{domain}'
    elif group and org:
        search_dn = f'cn={group},ou={org},{domain}'
    elif org:
        search_dn = f'ou={org},{domain}'
    else:
        search_dn = f'{domain}'
    try:
        # Attempt to list groups and return results
        results = list_groups(search_dn, search_attribute)
        return results
    except Exception as e:
        return {'error': str(e)}

@app.route('/delete', methods=['GET'])
def delete():
    user = request.args.get('user')
    group = request.args.get('group')
    org = request.args.get('org')
    ldap_password = request.args.get('ldap_password')
    if user and org:
        delete_dn = f'uid={user},ou={org},{domain}'
    elif group and org:
        delete_dn = f'cn={group},ou={org},{domain}'
    elif org:
        delete_dn = f'ou={org},{domain}'
    else:
        return 'Wrong inputs.', 400
    try:
        # Attempt to list groups and return results
        run_delete(ldap_password, delete_dn)
        return f'{delete_dn} deleted successfully.'
    except Exception as e:
        return f'Error deleting group: {str(e)}', 500
           
def get_next_available_uid():
    command = [
        'ldapsearch',
        '-x',
        '-LLL',
        '-H', f'{uri}',
        '-b', f'{domain}',
        '(objectClass=inetOrgPerson)',
        'uidNumber'
    ]
    
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    if result.returncode != 0:
        print(f"Error executing ldapsearch: {result.stderr}")
        return None

    uid_numbers = [int(match) for match in re.findall(r'uidNumber: (\d+)', result.stdout)]
    
    if not uid_numbers:
        print("No uidNumbers found.")
        return None
    
    next_available_uid = max(uid_numbers) + 1
    
    return next_available_uid

def get_next_available_gid():
    command = [
        'ldapsearch',
        '-x',
        '-LLL',
        '-H', f'{uri}',
        '-b', f'{group_search_base}',
        '(objectClass=*)',
        'gidNumber'
    ]
    
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    if result.returncode != 0:
        print(f"Error executing ldapsearch: {result.stderr}")
        return None

    gid_numbers = [int(match) for match in re.findall(r'gidNumber: (\d+)', result.stdout)]
    if not gid_numbers:
        print("No gidNumber found.")
        return None
    
    next_available_gid = max(gid_numbers) + 1
    
    return next_available_gid

def get_available_group_gid(group, group_base):
    command = [
        'ldapsearch',
        '-x',
        '-LLL',
        '-H', f'{uri}',
        '-b', f'cn={group},{group_base}',
        '(objectClass=*)',
        'gidNumber'
    ]
    
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    if result.returncode != 0:
        print(f"Error executing ldapsearch: {result.stderr}")
        return None

    gid_number = re.findall(r'gidNumber: (\d+)', result.stdout)
    return gid_number[0]

def generate_ssha_password(password):
    command = ['slappasswd', '-h', '{SSHA}', '-s', password]
    
    try:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error generating SSHA password: {e.stderr}"

def list_groups(search_dn, search_attribute):
    command = [
        'ldapsearch',
        '-x',
        '-LLL',
        '-H', f'{uri}',
        '-b', f'{search_dn}',
        '(objectClass=*)',
        f'{search_attribute}'
    ]
    
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    print("Standard Output:\n", result.stdout)
    return result.stdout
    
def generate_ldif_user(username, uid_number, group, gid_number, password_hash, user_base, group_base):
    return f"""
dn: uid={username},{user_base}
objectClass: inetOrgPerson
objectClass: posixAccount
objectClass: top
cn: {username}
sn: {username}
uid: {username}
uidNumber: {uid_number}
gidNumber: {gid_number}
homeDirectory: /home/{username}
loginShell: /bin/bash
mail: {username}@example.com
userPassword: {password_hash}

dn: cn={group},{group_base}
changetype: modify
add: memberUid
memberUid: {username}
"""

def generate_ldif_group(group, gid_number, group_base):
    return f"""
dn: cn={group},{group_base}
objectClass: posixGroup
objectClass: top
cn: {group}
gidNumber: {gid_number}
"""

def generate_ldif_org(org):
    return f"""
dn: ou={org},{domain}
objectClass: organizationalUnit
ou: {org}
"""

def run_delete(ldap_password, delete_dn):
    subprocess.run(['ldapdelete', '-x', '-D', f'{binddn}', '-w', ldap_password, delete_dn], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return print(f"{delete_dn} deleted successfully.")

def run_ldif(file_path, ldap_password):
    subprocess.run(['ldapadd', '-x', '-D', f'{binddn}', '-w', ldap_password, '-f', file_path], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print("LDIF file processed successfully.")
    os.remove(file_path)
    print(f"{file_path} deleted successfully.")

if __name__ == '__main__':
    app.run(host='master-node', port=5001, debug=True)
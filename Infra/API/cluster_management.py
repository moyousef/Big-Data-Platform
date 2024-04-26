from flask import Flask, request, jsonify
import subprocess
import yaml

yaml_file_path = "/home/wakeb/Big-Data-Platform/Infra/API/environmentvariables.yaml"

with open(yaml_file_path, 'r') as yaml_file:
    config = yaml.safe_load(yaml_file)

bash_path = config['cluster']['bash_path']
creds_path = config['cluster']['creds_path']
config_auto_path = config['cluster']['config_auto_path']

app = Flask(__name__)

@app.route('/cluster/create', methods=['POST'])
def create():
    data = request.json
    args_list = data.get('workers', [])
    master = data.get('master')
    if master is None:
        return jsonify({'error': 'master must be defined'}), 400

    with open(creds_path, 'r') as file:
        lines = file.readlines()
    if args_list:
        hosts = [f'"{h}"' for h in args_list]
        workers = ' '.join(hosts)
        replace_dict = {
        'master_ip=': f'master_ip="{master}"\n',
        'workers_ips=': f'workers_ips=({workers})\n',
        'machines_ips': f'machines_ips=("{master}" {workers})\n'
    }
    else:
        replace_dict = {
        'master_ip=': f'master_ip="{master}"\n',
        'workers_ips=': 'workers_ips=\n',
        'machines_ips': f'machines_ips=("{master}")\n'
    }
    for i, line in enumerate(lines):
        for key, value in replace_dict.items():
            if key in line:
                if callable(value):
                    lines[i] = value(line)
                else:
                    lines[i] = value
                break
    content = ''.join(lines)
    with open(creds_path, 'w') as file:
        file.write(content)
        
    command = ['./install.sh']
    print(command)
    try:
        result = subprocess.run(command, check=True, text=True, capture_output=True, cwd=bash_path)
        output = result.stdout
        error = result.stderr
        return_code = result.returncode
    except subprocess.CalledProcessError as e:
        output = e.stdout
        error = e.stderr
        return_code = e.returncode

    return output

@app.route('/cluster/add_nodes', methods=['POST'])
def add_nodes():
    data = request.json
    args_list = data.get('workers', [])

    command = ['./install.sh'] + args_list
    print(command)
    try:
        result = subprocess.run(command, check=True, text=True, capture_output=True, cwd=bash_path)
        output = result.stdout
        error = result.stderr
        return_code = result.returncode
    except subprocess.CalledProcessError as e:
        output = e.stdout
        error = e.stderr
        return_code = e.returncode

    return output

@app.route('/cluster/remove_nodes', methods=['POST'])
def remove_nodes():
    data = request.json
    args_list = data.get('workers', [])

    command = ['python3', config_auto_path + '/down_scaling.py'] + args_list
    print(command)
    try:
        result = subprocess.run(command, check=True, text=True, capture_output=True)
        output = result.stdout
        error = result.stderr
        return_code = result.returncode
    except subprocess.CalledProcessError as e:
        output = e.stdout
        error = e.stderr
        return_code = e.returncode

    return output

if __name__ == '__main__':
    app.run(host='master-node', port=5002, debug=True)
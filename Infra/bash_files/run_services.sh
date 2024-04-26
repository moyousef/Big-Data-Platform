#!/bin/bash

source credentials.env

num_of_workers=${#workers_ips[@]}

# SSH key file and unix_user
ssh_key_path="~/.ssh/id_rsa"

# List of new ips
new_workers_ips=()

# to be updated
merged_workers_ips=()
num_of_fixed_nodes=$((${#workers_ips[@]} + 1))
num_of_new_nodes=0
total_num_of_nodes=0

#  _______  _______  _______           _______  _______  _       _________ _______ 
# (  ___  )(  ____ )(  ____ \|\     /|(       )(  ____ \( (    /|\__   __/(  ____ \
# | (   ) || (    )|| (    \/| )   ( || () () || (    \/|  \  ( |   ) (   | (    \/
# | (___) || (____)|| |      | |   | || || || || (__    |   \ | |   | |   | (_____ 
# |  ___  ||     __)| | ____ | |   | || |(_)| ||  __)   | (\ \) |   | |   (_____  )
# | (   ) || (\ (   | | \_  )| |   | || |   | || (      | | \   |   | |         ) |
# | )   ( || ) \ \__| (___) || (___) || )   ( || (____/\| )  \  |   | |   /\____) |
# |/     \||/   \__/(_______)(_______)|/     \|(_______/|/    )_)   )_(   \_______)

function read_args(){
    if [ "$#" -eq 0 ]; then
        echo "No arguments provided"
    else
        for ((i = 1; i <= $#; i++)); do
            new_workers_ips+=("${!i}")
        done
        echo "New hosts: ${new_workers_ips[@]}"
        echo "Number of new hosts: ${#new_workers_ips[@]}"
    fi
}

#  _______  _______  _______ _________ _______  _______            _______  _______  _______          _________ _______  _______  _______ 
# (       )(  ___  )(  ____ \\__   __/(  ____ \(  ____ )          (  ____ \(  ____ \(  ____ )|\     /|\__   __/(  ____ \(  ____ \(  ____ \
# | () () || (   ) || (    \/   ) (   | (    \/| (    )|          | (    \/| (    \/| (    )|| )   ( |   ) (   | (    \/| (    \/| (    \/
# | || || || (___) || (_____    | |   | (__    | (____)|          | (_____ | (__    | (____)|| |   | |   | |   | |      | (__    | (_____ 
# | |(_)| ||  ___  |(_____  )   | |   |  __)   |     __)          (_____  )|  __)   |     __)( (   ) )   | |   | |      |  __)   (_____  )
# | |   | || (   ) |      ) |   | |   | (      | (\ (                   ) || (      | (\ (    \ \_/ /    | |   | |      | (            ) |
# | )   ( || )   ( |/\____) |   | |   | (____/\| ) \ \__          /\____) || (____/\| ) \ \__  \   /  ___) (___| (____/\| (____/\/\____) |
# |/     \||/     \|\_______)   )_(   (_______/|/   \__/          \_______)(_______/|/   \__/   \_/   \_______/(_______/(_______/\_______)
                                                                                                                                
function start_mysql_service() {
    echo "Starting mysql service on master node..."
    ssh -o StrictHostKeyChecking=no -i "$ssh_key_path" "$unix_user@$master_ip" "
        printf '%s\n' '$password' | sudo -S service mysql start
    "
}

function start_grafana_service() {
    echo "Starting grafana service on master node..."
    ssh -o StrictHostKeyChecking=no -i "$ssh_key_path" "$unix_user@$master_ip" "
        printf '%s\n' '$password' | sudo -S service grafana-server start
    "
}

function start_infuxdb_service() {
    echo "Starting influxdb service on master node..."
    ssh -o StrictHostKeyChecking=no -i "$ssh_key_path" "$unix_user@$master_ip" "
        printf '%s\n' '$password' | sudo -S service influxdb start
    "
}

function start_hive_service() {

    HADOOP_HOME="$hadoop_cluster/hadoop-3.3.5"

    echo "Starting hive service on master node..."
    ssh -o StrictHostKeyChecking=no -i "$ssh_key_path" "$unix_user@$master_ip" "
        export HADOOP_HOME=$HADOOP_HOME
        nohup $hadoop_cluster/apache-hive-3.1.3-bin/bin/hive --service metastore > /dev/null 2>&1 &
        nohup $hadoop_cluster/apache-hive-3.1.3-bin/bin/hive --service hiveserver2 > /dev/null 2>&1 &
    "
}

function start_airflow_service() {

    echo "Starting Airflow service on master node..."
    ssh -o StrictHostKeyChecking=no -i "$ssh_key_path" "$unix_user@$master_ip" "
        nohup airflow webserver > /dev/null 2>&1 &
        nohup airflow scheduler > /dev/null 2>&1 &
        nohup airflow celery worker > /dev/null 2>&1 &
    "
}

#           _______  _______  _        _______  _______            _______  _______  _______          _________ _______  _______  _______ 
# |\     /|(  ___  )(  ____ )| \    /\(  ____ \(  ____ )          (  ____ \(  ____ \(  ____ )|\     /|\__   __/(  ____ \(  ____ \(  ____ \
# | )   ( || (   ) || (    )||  \  / /| (    \/| (    )|          | (    \/| (    \/| (    )|| )   ( |   ) (   | (    \/| (    \/| (    \/
# | | _ | || |   | || (____)||  (_/ / | (__    | (____)|          | (_____ | (__    | (____)|| |   | |   | |   | |      | (__    | (_____ 
# | |( )| || |   | ||     __)|   _ (  |  __)   |     __)          (_____  )|  __)   |     __)( (   ) )   | |   | |      |  __)   (_____  )
# | || || || |   | || (\ (   |  ( \ \ | (      | (\ (                   ) || (      | (\ (    \ \_/ /    | |   | |      | (            ) |
# | () () || (___) || ) \ \__|  /  \ \| (____/\| ) \ \__          /\____) || (____/\| ) \ \__  \   /  ___) (___| (____/\| (____/\/\____) |
# (_______)(_______)|/   \__/|_/    \/(_______/|/   \__/          \_______)(_______/|/   \__/   \_/   \_______/(_______/(_______/\_______)


function start_redis_service() {

    if [ "$num_of_new_nodes" -eq 0 ]; then

        echo "Starting redis service on master node..."
        ssh -o StrictHostKeyChecking=no -i "$ssh_key_path" "$unix_user@$master_ip" "
            sudo service redis-server start
        "

        echo "Starting redis service on worker nodes..."
        for ((i = 0; i < num_of_workers; i++))
        do
            echo "Connecting to ${workers_ips[$i]}..."
            ssh -o StrictHostKeyChecking=no -i "$ssh_key_path" "$unix_user@${workers_ips[$i]}" "
                sudo service redis-server start
            "
        done

    else

        echo "Starting redis service on new worker nodes..."
        for ((i = 0; i < num_of_new_nodes; i++))
        do
            echo "Connecting to ${new_workers_ips[$i]}..."
            ssh -o StrictHostKeyChecking=no -i "$ssh_key_path" "$unix_user@${new_workers_ips[$i]}" "
                sudo service redis-server start
            "
        done
    fi
}

function start_hadoop() {

    if [ "$num_of_new_nodes" -eq 0 ]; then

        echo "Starting hadoop service on master node..."
        ssh -o StrictHostKeyChecking=no -i "$ssh_key_path" "$unix_user@$master_ip" "
            $hadoop_cluster/hadoop-3.3.5/sbin/start-dfs.sh 
            $hadoop_cluster/hadoop-3.3.5/sbin/start-yarn.sh
        "

        echo "Starting hadoop service on worker nodes..."
        for ((i = 0; i < num_of_workers; i++))
        do
            echo "Connecting to ${workers_ips[$i]}..."
            ssh -o StrictHostKeyChecking=no -i "$ssh_key_path" "$unix_user@${workers_ips[$i]}" "
                $hadoop_cluster/hadoop-3.3.5/sbin/start-dfs.sh 
                $hadoop_cluster/hadoop-3.3.5/sbin/start-yarn.sh
            "
        done

    else

        echo "Starting hadoop service on new worker nodes..."
        for ((i = 0; i < num_of_new_nodes; i++))
        do
            echo "Connecting to ${new_workers_ips[$i]}..."
            ssh -o StrictHostKeyChecking=no -i "$ssh_key_path" "$unix_user@${new_workers_ips[$i]}" "
                $hadoop_cluster/hadoop-3.3.5/sbin/start-dfs.sh 
                $hadoop_cluster/hadoop-3.3.5/sbin/start-yarn.sh
            "
        done
    fi
}

function start_zookeeper() {

    if [ "$num_of_new_nodes" -eq 0 ]; then

        echo "Starting Zookeeper service on master node..."
        ssh -o StrictHostKeyChecking=no -i "$ssh_key_path" "$unix_user@$master_ip" "
            nohup $hadoop_cluster/kafka_2.12-3.4.0/bin/zookeeper-server-start.sh $hadoop_cluster/kafka_2.12-3.4.0/config/zookeeper.properties > /dev/null 2>&1 &
        "

        echo "Starting Zookeeper service on worker nodes..."
        for ((i = 0; i < num_of_workers; i++)); do
            echo "Connecting to ${workers_ips[$i]}..."
            ssh -o StrictHostKeyChecking=no -i "$ssh_key_path" "$unix_user@${workers_ips[$i]}" "
                nohup $hadoop_cluster/kafka_2.12-3.4.0/bin/zookeeper-server-start.sh $hadoop_cluster/kafka_2.12-3.4.0/config/zookeeper.properties > /dev/null 2>&1 &
            "
        done
    else

        echo "Starting Zookeeper service on new worker nodes..."
        for ((i = 0; i < num_of_new_nodes; i++)); do
            echo "Connecting to ${new_workers_ips[$i]}..."
            ssh -o StrictHostKeyChecking=no -i "$ssh_key_path" "$unix_user@${new_workers_ips[$i]}" "
                nohup $hadoop_cluster/kafka_2.12-3.4.0/bin/zookeeper-server-start.sh $hadoop_cluster/kafka_2.12-3.4.0/config/zookeeper.properties > /dev/null 2>&1 &
            "
        done

    fi

}

function start_nifi() {

    if [ "$num_of_new_nodes" -eq 0 ]; then

        echo "Starting NiFi service on master node..."
        ssh -o StrictHostKeyChecking=no -i "$ssh_key_path" "$unix_user@$master_ip" "
            $hadoop_cluster/nifi-1.22.0/bin/nifi.sh start  > /dev/null 2>&1 &
        "

        echo "Starting NiFi service on worker nodes..."
        for ((i = 0; i < num_of_workers; i++))
        do
            echo "Connecting to ${workers_ips[$i]}..."
            ssh -o StrictHostKeyChecking=no -i "$ssh_key_path" "$unix_user@${workers_ips[$i]}" "
                $hadoop_cluster/nifi-1.22.0/bin/nifi.sh start  > /dev/null 2>&1 &
            "
        done

    else
    
        echo "Starting NiFi service on new worker nodes..."
        for ((i = 0; i < num_of_new_nodes; i++))
        do
            echo "Connecting to ${new_workers_ips[$i]}..."
            ssh -o StrictHostKeyChecking=no -i "$ssh_key_path" "$unix_user@${new_workers_ips[$i]}" "
                $hadoop_cluster/nifi-1.22.0/bin/nifi.sh start  > /dev/null 2>&1 &
            "
        done
    fi
}

function start_kafka() {

    if [ "$num_of_new_nodes" -eq 0 ]; then
        
        echo "Starting Kafka service on master node..."
        ssh -o StrictHostKeyChecking=no -i "$ssh_key_path" "$unix_user@$master_ip" "
            nohup $hadoop_cluster/kafka_2.12-3.4.0/bin/kafka-server-start.sh $hadoop_cluster/kafka_2.12-3.4.0/config/server.properties > /dev/null 2>&1 &
        "

        echo "Starting Kafka service on worker nodes..."
        for ((i = 0; i < num_of_workers; i++))
        do
            echo "Connecting to ${workers_ips[$i]}..."
            ssh -o StrictHostKeyChecking=no -i "$ssh_key_path" "$unix_user@${workers_ips[$i]}" "
                nohup $hadoop_cluster/kafka_2.12-3.4.0/bin/kafka-server-start.sh $hadoop_cluster/kafka_2.12-3.4.0/config/server.properties > /dev/null 2>&1 &
            "
        done
    else
    
        echo "Starting Kafka service on new worker nodes..."
        for ((i = 0; i < num_of_new_nodes; i++))
        do
            echo "Connecting to ${new_workers_ips[$i]}..."
            ssh -o StrictHostKeyChecking=no -i "$ssh_key_path" "$unix_user@${new_workers_ips[$i]}" "
                nohup $hadoop_cluster/kafka_2.12-3.4.0/bin/kafka-server-start.sh $hadoop_cluster/kafka_2.12-3.4.0/config/server.properties > /dev/null 2>&1 &
            "
        done
    fi

}
function srart_prometheus_service() {

    if [ "$num_of_new_nodes" -eq 0 ]; then

        PROMETHEUS_HOME="$hadoop_cluster/prometheus-2.48.0-rc.0.linux-amd64"
        NODE_EXPORTER_HOME="$hadoop_cluster/node_exporter-1.6.1.linux-amd64"

        echo "Starting prometheus service on master node..."
        ssh -o StrictHostKeyChecking=no -i "$ssh_key_path" "$unix_user@$master_ip" "
            $PROMETHEUS_HOME/prometheus --config.file=$PROMETHEUS_HOME/prometheus.yml --web.enable-lifecycle > /dev/null 2>&1 &
            $NODE_EXPORTER_HOME/node_exporter --web.listen-address=:9100 > /dev/null 2>&1 &
        "

        echo "Starting prometheus service on worker nodes..."
        for ((i = 0; i < num_of_workers; i++))
        do
            echo "Connecting to ${workers_ips[$i]}..."
            ssh -o StrictHostKeyChecking=no -i "$ssh_key_path" "$unix_user@${workers_ips[$i]}" "
                $NODE_EXPORTER_HOME/node_exporter --web.listen-address=:9100 > /dev/null 2>&1 &
            "
        done
    else

        echo "Reloading prometheus service on master node..."
        ssh -o StrictHostKeyChecking=no -i "$ssh_key_path" "$unix_user@$master_ip" "
            curl -X POST http://$master_ip:9090/-/reload
        "

        echo "Starting prometheus service on new worker nodes..."
        for ((i = 0; i < num_of_new_nodes; i++))
        do
            echo "Connecting to ${new_workers_ips[$i]}..."
            ssh -o StrictHostKeyChecking=no -i "$ssh_key_path" "$unix_user@${new_workers_ips[$i]}" "
                $NODE_EXPORTER_HOME/node_exporter --web.listen-address=:9100 > /dev/null 2>&1 &
            "
        done
    fi
}

function start_spark(){

    if [ "$num_of_new_nodes" -eq 0 ]; then

        echo "Starting Spark service on master node..."
        ssh -o StrictHostKeyChecking=no -i "$ssh_key_path" "$unix_user@$master_ip" "
            $hadoop_cluster/spark-3.4.1-bin-hadoop3/sbin/start-master.sh
        "

        echo "Starting Spark service on worker nodes..."
        for ((i = 0; i < num_of_workers; i++))
        do
            echo "Connecting to ${workers_ips[$i]}..."
            ssh -o StrictHostKeyChecking=no -i "$ssh_key_path" "$unix_user@${workers_ips[$i]}" "
                $hadoop_cluster/spark-3.4.1-bin-hadoop3/sbin/start-worker.sh spark://$master_ip:7077
            "
        done
    else

        echo "Starting Spark service on new worker nodes..."
        for ((i = 0; i < num_of_new_nodes; i++))
        do
            echo "Connecting to ${new_workers_ips[$i]}..."
            ssh -o StrictHostKeyChecking=no -i "$ssh_key_path" "$unix_user@${new_workers_ips[$i]}" "
                $hadoop_cluster/spark-3.4.1-bin-hadoop3/sbin/start-worker.sh spark://$master_ip:7077
            "
        done
    fi
}

#  _______ _________ _______  _______ _________           _______ _________ _______  _______  _       _________ _        _______
# (  ____ \\__   __/(  ___  )(  ____ )\__   __/          (  ____ )\__   __/(  ____ )(  ____ \( \      \__   __/( (    /|(  ____ \
# | (    \/   ) (   | (   ) || (    )|   ) (             | (    )|   ) (   | (    )|| (    \/| (         ) (   |  \  ( || (    \/
# | (_____    | |   | (___) || (____)|   | |             | (____)|   | |   | (____)|| (__    | |         | |   |   \ | || (__
# (_____  )   | |   |  ___  ||     __)   | |             |  _____)   | |   |  _____)|  __)   | |         | |   | (\ \) ||  __)
#       ) |   | |   | (   ) || (\ (      | |             | (         | |   | (      | (      | |         | |   | | \   || (
# /\____) |   | |   | )   ( || ) \ \__   | |             | )      ___) (___| )      | (____/\| (____/\___) (___| )  \  || (____/\
# \_______)   )_(   |/     \||/   \__/   )_(             |/       \_______/|/       (_______/(_______/\_______/|/    )_)(_______/


# read new nodes from args and merge them with the fixed nodes
read_args "$@"
num_of_new_nodes=${#new_workers_ips[@]}
total_num_of_nodes=$(($num_of_fixed_nodes + $num_of_new_nodes))
merged_workers_ips=("${workers_ips[@]}" "${new_workers_ips[@]}")

echo "Total number of nodes: $total_num_of_nodes"
echo "Merged worker nodes: ${merged_workers_ips[@]}"


function run_all(){

    # services to be started on master node
    if [ "$num_of_new_nodes" -eq 0 ]; then
        echo "Starting services on master node..."
        start_mysql_service
        start_grafana_service
        start_infuxdb_service
    fi

    start_redis_service
    start_hadoop

    start_zookeeper
    start_nifi
    start_kafka

    if [ "$num_of_new_nodes" -eq 0 ]; then
        echo "Starting services on master node..."
        start_hive_service
    fi

    if [ "$num_of_new_nodes" -eq 0 ]; then
        start_airflow_service
    fi

    srart_prometheus_service
    start_spark
}

run_all

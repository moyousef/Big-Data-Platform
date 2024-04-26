#!/bin/bash

###########################################################################################################
############################################## All variables ##############################################
###########################################################################################################

# List of private and public IPs corresponding to each host
private_ips=("192.168.190.111" "192.168.190.112" "192.168.190.113")
public_ips=("192.168.190.111" "192.168.190.112" "192.168.190.113")

# Credentials
username="wakeb"
total_num_of_nodes=${#public_ips[@]}
password='Wakeb@!2080@$!'


#    _______  _______  _______ _________ _______  _______          _______ _________ _        _______  _______ 
#   (       )(  ___  )(  ____ \\__   __/(  ____ \(  ____ )        (  ____ \\__   __/( \      (  ____ \(  ____ \
#   | () () || (   ) || (    \/   ) (   | (    \/| (    )|        | (    \/   ) (   | (      | (    \/| (    \/
#   | || || || (___) || (_____    | |   | (__    | (____)|        | (__       | |   | |      | (__    | (_____ 
#   | |(_)| ||  ___  |(_____  )   | |   |  __)   |     __)        |  __)      | |   | |      |  __)   (_____  )
#   | |   | || (   ) |      ) |   | |   | (      | (\ (           | (         | |   | |      | (            ) |
#   | )   ( || )   ( |/\____) |   | |   | (____/\| ) \ \__        | )      ___) (___| (____/\| (____/\/\____) |
#   |/     \||/     \|\_______)   )_(   (_______/|/   \__/        |/       \_______/(_______/(_______/\_______)
                                                                                                                 
                                                                                            
function remove_influx_master(){

    echo "connecting to ${public_ips[0]}... to remove influx"
    ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_rsa "$username@${public_ips[0]}" "
        printf '%s\n' '$password' | sudo -S systemctl stop influxdb
        printf '%s\n' '$password' | sudo -S rm  /root/.influxdbv2/configs
        printf '%s\n' '$password' | sudo -S apt remove influxdb2 influxdb2-cli -y
        printf '%s\n' '$password' | sudo -S apt -y purge influxdb2
        printf '%s\n' '$password' | sudo -S rm /etc/apt/sources.list.d/influxdata.list
        printf '%s\n' '$password' | sudo -S apt autoclean && printf '%s\n' '$password' -y | sudo -S apt autoremove -y
        printf '%s\n' '$password' | sudo -S rm -rf /var/lib/influxdb/
        printf '%s\n' '$password' | sudo -S rm -rf /var/log/influxdb/
        printf '%s\n' '$password' | sudo -S rm -rf /etc/influxdb/
        printf '%s\n' '$password' | sudo -S rm -rf ~/.influxdbv2
    "
}

function remove_grafana_master(){

    echo "connecting to ${public_ips[0]}... to remove grafana"
    ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_rsa "$username@${public_ips[0]}" "
        printf '%s\n' '$password' | sudo -S service grafana-server stop
        printf '%s\n' '$password' | sudo -S apt-get remove grafana -y
        printf '%s\n' '$password' | sudo -S rm -i /etc/apt/sources.list.d/grafana.list
    "
}

function remove_mysql_master(){

    echo "connecting to ${public_ips[0]}... to remove mysql"
    ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_rsa "$username@${public_ips[0]}" "
        printf '%s\n' '$password' | sudo -S service mysql stop
        printf '%s\n' '$password' | sudo -S apt-get purge mysql-server mysql-client mysql-common mysql-server-core-* mysql-client-core-* -y
        printf '%s\n' '$password' | sudo -S rm -rf /var/lib/mysql
        printf '%s\n' '$password' | sudo -S rm -rf /etc/mysql /etc/my.cnf
        printf '%s\n' '$password' | sudo -S apt autoremove -y
    "
}

#    _______  _        _              _        _______  ______   _______  _______          _______ _________ _        _______  _______ 
#   (  ___  )( \      ( \            ( (    /|(  ___  )(  __  \ (  ____ \(  ____ \        (  ____ \\__   __/( \      (  ____ \(  ____ \
#   | (   ) || (      | (            |  \  ( || (   ) || (  \  )| (    \/| (    \/        | (    \/   ) (   | (      | (    \/| (    \/
#   | (___) || |      | |            |   \ | || |   | || |   ) || (__    | (_____         | (__       | |   | |      | (__    | (_____ 
#   |  ___  || |      | |            | (\ \) || |   | || |   | ||  __)   (_____  )        |  __)      | |   | |      |  __)   (_____  )
#   | (   ) || |      | |            | | \   || |   | || |   ) || (            ) |        | (         | |   | |      | (            ) |
#   | )   ( || (____/\| (____/\      | )  \  || (___) || (__/  )| (____/\/\____) |        | )      ___) (___| (____/\| (____/\/\____) |
#   |/     \|(_______/(_______/      |/    )_)(_______)(______/ (_______/\_______)        |/       \_______/(_______/(_______/\_______)
                                                                                                                                        

function remove_nifi(){

    NIFI_HOME="/home/wakeb/hadoop/nifi-1.22.0"

    for ((i = 0; i < total_num_of_nodes; i++))
    do 
        echo "Connecting to ${public_ips[$i]}... to remove nifi"
        ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_rsa "$username@${public_ips[$i]}" "
            # Stop nifi services (change this according to your nifi version)
            $NIFI_HOME/bin/nifi.sh stop
            rm -rf $NIFI_HOME
        "
    done
}

function remove_kafka_and_zookeeper(){
    
        KAFKA_HOME="/home/wakeb/hadoop/kafka_2.12-3.4.0"
    
        for ((i = 0; i < total_num_of_nodes; i++))
        do 
            echo "Connecting to ${public_ips[$i]}... to remove kafka"
            ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_rsa "$username@${public_ips[$i]}" "
                # Stop Kafka services (change this according to your Kafka version)
                $KAFKA_HOME/bin/kafka-server-stop.sh
                $KAFKA_HOME/bin/zookeeper-server-stop.sh
                rm -rf $KAFKA_HOME
                rm -rf /tmp/kafka-logs
            "
        done
}

function remove_spark(){
    
    SPARK_HOME="/home/wakeb/hadoop/spark-3.4.1-bin-hadoop3"

    # stop spark on the master node
    echo "Connecting to ${public_ips[0]}... to remove spark"
    ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_rsa "$username@${public_ips[0]}" "
        # Stop spark services (change this according to your spark version)
        $SPARK_HOME/sbin/stop-master.sh
        rm -rf $SPARK_HOME
    "

    # stop spark on the worker nodes
    for ((i = 1; i < total_num_of_nodes; i++))
    do 
        echo "Connecting to ${public_ips[$i]}... to remove spark"
        ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_rsa "$username@${public_ips[$i]}" "
            # Stop spark services (change this according to your spark version)
            $SPARK_HOME/sbin/stop-worker.sh
            rm -rf $SPARK_HOME
        "
    done
}


function remove_hive(){
    
    HIVE_HOME="/home/wakeb/hadoop/apache-hive-3.1.3-bin"

    # stop hive on the master node then remove it
    echo "Stop hive services on the master"
    ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_rsa "$username@${public_ips[0]}" "
        # Stop hive services (change this according to your hive version)
        pkill -f hive-metastore
    "

    # remove hive on the worker nodes
    for ((i = 0; i < total_num_of_nodes; i++))
    do 
        echo "Connecting to ${public_ips[$i]}... to remove hive"
        ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_rsa "$username@${public_ips[$i]}" "
            rm -r /home/wakeb/hadoop/apache-hive-3.1.3-bin
        "
    done

}

function remove_prometheus(){
    
    PROMETHEUS_HOME="/home/wakeb/hadoop/prometheus-2.48.0-rc.0.linux-amd64"
    NODE_EXPORTER_HOME="/home/wakeb/hadoop/node_exporter-1.6.1.linux-amd64"

    ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_rsa "$username@${public_ips[0]}" "
        # Stop prometheus services (change this according to your prometheus version)
        pkill -f prometheus
        pkill -f node_expo
        rm -rf $PROMETHEUS_HOME
        rm -rf $NODE_EXPORTER_HOME
    "

    # remove prometheus on the worker nodes
    for ((i = 1; i < total_num_of_nodes; i++))
    do 
        echo "Connecting to ${public_ips[$i]}... to remove prometheus"
        ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_rsa "$username@${public_ips[$i]}" "
            # Stop prometheus services (change this according to your prometheus version)
            pkill -f node_expo
            rm -rf $NODE_EXPORTER_HOME
        "
    done
}

function remove_airflow(){

    AIRFLOW_HOME="/home/wakeb/airflow"

    # stop airflow on the master node then remove it
    echo "Stop airflow services on the master"
    ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_rsa "$username@${public_ips[0]}" "
        # Stop airflow services (change this according to your airflow version)
        pkill -f "airflow scheduler"
        pkill -f "airflow webserver"
        rm -rf $AIRFLOW_HOME
    "

    # remove airflow on the worker nodes
    for ((i = 0; i < total_num_of_nodes; i++))
    do 
        echo "Connecting to ${public_ips[$i]}... to remove airflow"
        ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_rsa "$username@${public_ips[$i]}" "
            kill $(cat /home/wakeb/airflow/airflow-worker.pid)
            rm -rf $AIRFLOW_HOME
        "
    done

}

function remove_hadoop(){

    HADOOP_HOME="/home/wakeb/hadoop/hadoop-3.3.5"

    for ((i = 0; i < total_num_of_nodes; i++))
    do 
        echo "Connecting to ${public_ips[$i]}... to remove hadoop"
        ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_rsa "$username@${public_ips[$i]}" "
            # Stop Hadoop services (change this according to your Hadoop version)
            $HADOOP_HOME/sbin/stop-dfs.sh
            $HADOOP_HOME/sbin/stop-yarn.sh
            $HADOOP_HOME/sbin/stop-all.sh
            rm -rf $HADOOP_HOME
            rm -rf /home/wakeb/hadoop
        "
    done
}

function remove_redis(){
    for ((i = 0; i < total_num_of_nodes; i++))
    do 
        echo "Connecting to ${public_ips[$i]}... to remove redis"
        ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_rsa "$username@${public_ips[$i]}" "
            printf '%s\n' '$password' | sudo -S service stop redis-server
            printf '%s\n' '$password' | sudo -S apt-get remove redis-server -y
            printf '%s\n' '$password' | sudo -S apt-get purge redis-server -y
            printf '%s\n' '$password' | sudo -S apt-get autoremove -y
            printf '%s\n' '$password' | sudo -S rm -rf /etc/redis
            printf '%s\n' '$password' | sudo -S rm -rf /var/lib/redis
        "
    done
}

#  _______  _______  ______   _______ 
# (  ____ \(  ___  )(  __  \ (  ____ \
# | (    \/| (   ) || (  \  )| (    \/
# | |      | |   | || |   ) || (__    
# | |      | |   | || |   | ||  __)   
# | |      | |   | || |   ) || (      
# | (____/\| (___) || (__/  )| (____/\
# (_______/(_______)(______/ (_______/
                                    

function remove_code(){

    CODE_HOME="/home/wakeb/Big-Data-Platform"

    for ((i = 0; i < total_num_of_nodes; i++))
    do 
        echo "Connecting to ${public_ips[$i]}..."
        ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_rsa "$username@${public_ips[$i]}" "
            rm -rf $CODE_HOME
        "
    done
}

function remove_github_access(){
    for ((i = 0; i < total_num_of_nodes; i++))
    do 
        echo "Connecting to ${public_ips[$i]}..."
        ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_rsa "$username@${public_ips[$i]}" "
            git config --global --unset user.name
            git config --global --unset user.email
            git config --global --unset user.password
            git config --global --unset credential.helper
        "
    done
}

#    _______  _______  _______  _        _______  _______  _______  _______ 
#   (  ____ )(  ___  )(  ____ \| \    /\(  ___  )(  ____ \(  ____ \(  ____ \
#   | (    )|| (   ) || (    \/|  \  / /| (   ) || (    \/| (    \/| (    \/
#   | (____)|| (___) || |      |  (_/ / | (___) || |      | (__    | (_____ 
#   |  _____)|  ___  || |      |   _ (  |  ___  || | ____ |  __)   (_____  )
#   | (      | (   ) || |      |  ( \ \ | (   ) || | \_  )| (            ) |
#   | )      | )   ( || (____/\|  /  \ \| )   ( || (___) || (____/\/\____) |
#   |/       |/     \|(_______/|_/    \/|/     \|(_______)(_______/\_______)

function remove_packages(){
    for ((i = 0; i < total_num_of_nodes; i++))
    do 
        echo "Connecting to ${public_ips[$i]}..."
        ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_rsa "$username@${public_ips[$i]}" "
            printf '%s\n' '$password' | sudo -S apt-get purge --auto-remove python3 python3-pip -y
            printf '%s\n' '$password' | sudo -S apt-get purge --auto-remove openjdk-* -y
            printf '%s\n' '$password' | sudo -S apt-get purge --auto-remove ansible -y
            printf '%s\n' '$password' | sudo -S apt-get autoremove -y
            printf '%s\n' '$password' | sudo -S apt-get clean -y
            printf '%s\n' '$password' | sudo -S rm -rf /usr/local/bin/pip*
            printf '%s\n' '$password' | sudo -S rm -rf /usr/local/lib/python*
        "
    done
}


#             _______  _______ _________ _______        _______  _        ______         _        _______           _______ 
#   |\     /|(  ___  )(  ____ \\__   __/(  ____ \      (  ___  )( (    /|(  __  \       | \    /\(  ____ \|\     /|(  ____ \
#   | )   ( || (   ) || (    \/   ) (   | (    \/      | (   ) ||  \  ( || (  \  )      |  \  / /| (    \/( \   / )| (    \/
#   | (___) || |   | || (_____    | |   | (_____       | (___) ||   \ | || |   ) |      |  (_/ / | (__     \ (_) / | (_____ 
#   |  ___  || |   | |(_____  )   | |   (_____  )      |  ___  || (\ \) || |   | |      |   _ (  |  __)     \   /  (_____  )
#   | (   ) || |   | |      ) |   | |         ) |      | (   ) || | \   || |   ) |      |  ( \ \ | (         ) (         ) |
#   | )   ( || (___) |/\____) |   | |   /\____) |      | )   ( || )  \  || (__/  )      |  /  \ \| (____/\   | |   /\____) |
#   |/     \|(_______)\_______)   )_(   \_______)      |/     \||/    )_)(______/       |_/    \/(_______/   \_/   \_______)
                                                                                                                            
function remove_hosts_file(){
    for ((i = 0; i < total_num_of_nodes; i++))
    do 
        echo "Connecting to ${public_ips[$i]}..."
        ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_rsa "$username@${public_ips[$i]}" "
            printf '%s\n' '$password' | sudo -S sed -i '/node/d' /etc/hosts
            printf '%s\n' '$password' | sudo -S sed -i '/public/d' /etc/hosts
        "
    done
}

function remove_key_files(){
    for ((i = 0; i < total_num_of_nodes; i++))
    do 
        echo "Connecting to ${public_ips[$i]}..."
        ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_rsa "$username@${public_ips[$i]}" "
            printf '%s\n' '$password' | sudo -S rm -rf ~/.ssh
        "
    done

    echo "Removing local ssh key..."
    rm -rf ~/.ssh/id_rsa
    rm -rf ~/.ssh/authorized_keys
}

#  _______ _________ _______  _______ _________   _______ _________ _______  _______  _       _________ _        _______ 
# (  ____ \\__   __/(  ___  )(  ____ )\__   __/  (  ____ )\__   __/(  ____ )(  ____ \( \      \__   __/( (    /|(  ____ \
# | (    \/   ) (   | (   ) || (    )|   ) (     | (    )|   ) (   | (    )|| (    \/| (         ) (   |  \  ( || (    \/
# | (_____    | |   | (___) || (____)|   | |     | (____)|   | |   | (____)|| (__    | |         | |   |   \ | || (__    
# (_____  )   | |   |  ___  ||     __)   | |     |  _____)   | |   |  _____)|  __)   | |         | |   | (\ \) ||  __)   
#       ) |   | |   | (   ) || (\ (      | |     | (         | |   | (      | (      | |         | |   | | \   || (      
# /\____) |   | |   | )   ( || ) \ \__   | |     | )      ___) (___| )      | (____/\| (____/\___) (___| )  \  || (____/\
# \_______)   )_(   |/     \||/   \__/   )_(     |/       \_______/|/       (_______/(_______/\_______/|/    )_)(_______/
                                                                                                                       

function remove_all(){
    remove_influx_master
    remove_grafana_master
    remove_mysql_master
    remove_nifi
    remove_kafka_and_zookeeper
    remove_spark
    remove_hive
    remove_prometheus
    remove_airflow
    remove_hadoop
    remove_redis
    remove_code
    remove_github_access
    remove_packages
    remove_hosts_file
    remove_key_files
}

remove_all


#!/bin/bash

pid_dir="$hadoop_cluster/temp/hadoopPID"
pid_files=("hadoop-wakeb-datanode.pid" "hadoop-wakeb-nodemanager.pid" "hadoop-wakeb-secondarynamenode.pid" "hadoop-wakeb-namenode.pid" "hadoop-wakeb-resourcemanager.pid")

# Flag to check if any PID file was found
pid_file_found=false

for file in "${pid_files[@]}"; do
    pid_file="$pid_dir/$file"
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null; then
            echo "$pid $file"
        else
            echo "$file is not running"
        fi
        pid_file_found=true
    fi
done

if [ "$pid_file_found" = false ]; then
    echo "Hadoop is Not Running."
fi

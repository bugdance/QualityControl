#!/bin/bash
kill -9 `ps -ef | grep quality_gun.py | awk '{print $2}' `
kill -9 `ps -ef | grep quality_count.py | awk '{print $2}' `
echo 3 > /proc/sys/vm/drop_caches
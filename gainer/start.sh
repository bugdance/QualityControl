#!/bin/bash
kill -9 `ps -ef | grep quality_gun.py | awk '{print $2}' `
kill -9 `ps -ef | grep quality_count.py | awk '{print $2}' `
echo 3 > /proc/sys/vm/drop_caches
rm -rf log/*.log
rm -rf img/*.png
rm -rf mp3/*.mp3
rm -rf pcm/*.pcm
rm -rf quality.log
rm -rf count.log
gunicorn -c quality_gun.py quality_receiver:app > /dev/null 2>&1 &
python3 quality_count.py > /dev/null 2>&1 &
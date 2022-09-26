#!/bin/bash
NODE=$1
NUM_NODES=$2
cd /home/{{ user }}/
python video_client.py ${NODE} ${NUM_NODES}

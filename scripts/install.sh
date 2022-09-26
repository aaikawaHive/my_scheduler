#!/bin/bash
cd /home/{{ user }}/
scp trn14:/persist/aaikawa/triton_client/video_client.py ./
scp trn14:/persist/aaikawa/copy.csv ./
apt update
apt install -y ffmpeg aria2
mkdir -p preds
touch done.txt
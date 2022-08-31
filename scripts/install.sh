#!/bin/bash
apt update
apt install -y zip htop screen libgl1-mesa-glx
cd /home/{{ user }}/DINO
pip install -r requirements.txt
cd models/dino/ops
python setup.py build install
python test.py
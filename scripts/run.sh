#!/bin/bash
NODE=$1
cd /home/{{ user }}/
cd detectron2/projects/MViTv2/
# pip install timm
# pip install opencv-python
# pip install shapely
#export NCCL_IBEXT_DISABLE=1
#export NCCL_IB_DISABLE=1
#export NCCL_DEBUG=INFO
#export NCCL_NET=Socket
#export NCCL_SOCKET_IFNAME=ibp129s0f1
#export GLOO_SOCKET_IFNAME=ibp129s0f1
#export NCCL_SOCKET_IFNAME=enp161s0f0
#export GLOO_SOCKET_IFNAME=enp161s0f0
export NCCL_SOCKET_IFNAME=enp161s0f0,enp129s0f0
# export NCCL_SOCKET_IFNAME=enp
# export GLOO_SOCKET_IFNAME=enp161s0f0,enp129s0f0
#export NCCL_SOCKET_IFNAME=enp129s0f1
#export GLOO_SOCKET_IFNAME=enp129s0f1

../../tools/lazyconfig_train_net.py --machine-rank $NODE --num-machines {{ num_nodes }} --dist-url="tcp://{{ main_ip }}:8686" \
    --num-gpus 8 --config-file configs/cascade_mask_rcnn_mvitv2_b_in21k_3x.py

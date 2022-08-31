#!/usr/bin/env python3
import argparse
import os
import sys
import csv
import yaml

from utils import run_parallel_command, config, cleanup, setup_logging

cwd = os.path.dirname(__file__)
cleanup('gpu')
cleanup('disk')
gpu_outputs, gpu_errs = setup_logging('gpu')
disk_outputs, disk_errs = setup_logging('disk')
hosts_file = os.path.join(cwd, 'hosts.txt')

SUBNET = '172.25.48.'
bad_hosts = ['154', '126', '82', '83', '84']
exclude = set(f'{SUBNET}{i}' for i in bad_hosts)
a40s = set(f'{SUBNET}{i}' for i in range(151, 166 + 1)) - exclude
a80s = set(f'{SUBNET}{i}' for i in range(122, 136 + 1)) - exclude
devs = (set(f'{SUBNET}{i}' for i in range(81, 90)) | set(f'{SUBNET}{i}' for i in range(111, 120))) - exclude

def gpu_available(file):
    """
    Reads from logfile to determine if entire node is free
    """
    reader = csv.reader(file, delimiter=',')
    max_usage = 0
    for row in reader:
        total, used = row
        total, used = float(total.split()[0]), float(used.split()[0])
        max_usage = max(max_usage, used)
    return max_usage / total < 0.02
        

def disk_available(min_disk, file):
    """
    Reads from logfile to determine if there is sufficient disk space
    """
    _, _, free, _, _ = file.readline().split()
    if 'G' in free:
        free = float(free[:-1])
    elif 'T' in free:
        free = float(free[:-1]) * 1e3
    else:
        print("invalid units for memory")
        exit(1)
    return free > min_disk

def host_search(args):
    """
    Searches for hosts that have no usage. Under use is defined
    as any GPU on the node has more than 5% of its GPU VRAM occupied
    """
    min_disk = args.min_disk
    host_list = args.gpu_type

    # get the gpu usage
    cmd = """
        nvidia-smi --query-gpu=memory.total,memory.used --format=csv | tail -n+2
    """
    run_parallel_command(host_list, 'parallel-ssh', cmd, stdout=gpu_outputs, stderr=gpu_errs)

    # get the disk usage
    drive = '/var/lib/docker'
    cmd = "df -h | grep " + drive + " | head -1 | cut -d' ' -f2- | sed 's/^[[:space:]]*//g'"
    run_parallel_command(host_list, 'parallel-ssh', cmd, stdout=disk_outputs, stderr=disk_errs)

    open_hosts = []
    for host in host_list:
        gpu, disk = os.path.join(gpu_outputs, host), os.path.join(disk_outputs, host)
        if os.path.getsize(gpu) == 0 or os.path.getsize(disk) == 0:
            continue
        with open(gpu, 'r') as g, open(disk, 'r') as d:
            if gpu_available(g) and disk_available(min_disk, d):
                open_hosts.append(host)
    print("available hosts: ", open_hosts)
    if len(open_hosts) < args.num_nodes:
        print(f"available hosts = {open_hosts} less than requested {args.num_nodes}")
        return 1
    saved_hosts = open(hosts_file, 'w')
    for host in open_hosts[:args.num_nodes]:
        saved_hosts.write(f"{host}\n")
    print("saved hosts: ", open_hosts[:args.num_nodes])

    if not args.save_logs:
        cleanup('gpu')
        cleanup('disk')

def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Utility for acquiring the host ips of machines that are not being used',
    )
    
    parser.add_argument('--num_nodes', metavar='NUM_NODES', type=int,
                         help='the number of required hosts, Overrides `config.yaml`')

    parser.add_argument('--min_disk', metavar='MIN_DISK', type=float,
                         help='the minimum required disk space for each host (in GB)')
    
    parser.add_argument('--gpu_type', type=int, choices=[10, 40, 80],
                         help='the type of gpus requested. Overrides `config.yaml`')
    
    parser.add_argument('--save_logs', action='store_true',
                         help='save stdout and stderr from hosts')

    args = parser.parse_args(argv)
    if args.gpu_type is None: 
        args.gpu_type = config['gpus']
    if args.gpu_type == 40:
        args.gpu_type = a40s
    elif args.gpu_type == 80:
        args.gpu_type = a80s
    elif args.gpu_type == 10:
        args.gpu_type = devs
    else:
        print(f"illegal value for gpu group : {args.gpu_type}")
        exit(1)
    if args.num_nodes is None:
        args.num_nodes = int(config['num_nodes'])
    if args.min_disk is None:
        args.min_disk = float(config['min_disk'])
    host_search(args)
    return 0

if __name__ == '__main__':
    sys.exit(main())
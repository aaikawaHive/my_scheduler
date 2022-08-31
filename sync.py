#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys
import pdb
import time
import yaml
from collections import defaultdict
from utils import config, hosts, parallel_rsync, remote_clean, remote_check_exists, run_parallel_command, setup_logging

logdir = 'sync'

def sync(args):
    """
    Copy `project` or `data` files specified in project_path to `/home/${USER}/` on the remote machine
    """
    n = len(hosts)
    logdirs = defaultdict(lambda : None)
    if args.save_logs:
        logdirs['stdout'], logdirs['stderr'] = setup_logging(logdir)
    src = config['project_path'] if args.sync_folder == 'project' else config['data_path']
    src = os.path.join(os.path.normpath(src), '') # this just ensures there's a trailing slash
    assert os.path.exists(src)
    base_directory = os.path.basename(os.path.normpath(src))
    remote_dst = f"/home/{config['user']}/{base_directory}" # this should not have a trailing slash

    if args.cleanup:
        td0 = time.time()
        remote_clean(hosts, remote_dst)
        print("--- {:2.4f} seconds for deletion ---".format(time.time() - td0))

    # Create the directory if it doesn't already exist
    cmd = """
        mkdir -p {} 
    """.format(remote_dst)
    run_parallel_command(hosts, 'parallel-ssh', cmd)
    t0 = time.time()
    assert remote_check_exists(hosts, remote_dst)

    # Ensure that the host has rsync installed
    cmd = """
        sudo apt install -y rsync
    """
    run_parallel_command(hosts, 'parallel-ssh', cmd)

    # Sync contents
    print('Size of src is: ')
    cmd = f"""
            du -h {src} | tail -n 1
        """
    print('{}'.format(subprocess.check_output(cmd, shell=True).decode('utf-8').strip()))
    print('Beginning rsync. Take your time...')
    t0 = time.time()
    p = parallel_rsync(hosts, src, remote_dst, **logdirs)
    while True: # process is alive
        try:
            p.wait(timeout=10)
            break
        except subprocess.TimeoutExpired:
            print("Time elapsed = {:2f}s".format(time.time() - t0))
            cmd = f"""
            --inline-stdout du -h {remote_dst} | tail -n 1
            """
            run_parallel_command(hosts, 'parallel-ssh', cmd)
        
    print("--- {:2.4f} seconds for copying ---".format(time.time() - t0))

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="""
        Utility for synchronizing project/data files across nodes specified in `hosts.txt`
        project folder names should be specified in `config.yaml`. Only copies files
        """,
    )
    
    parser.add_argument('sync_folder', type=str, default='project', choices=['project', 'data'],
                         help="pick either {'project', 'data'} to copy across hosts")
    
    parser.add_argument('--save_logs', action='store_true',
                         help='save stdout and stderr from hosts')

    parser.add_argument('--cleanup', action='store_true',
                         help='delete project/data folder before ')

    args = parser.parse_args()
    sync(args)
    return 0

if __name__ == '__main__':
    sys.exit(main())
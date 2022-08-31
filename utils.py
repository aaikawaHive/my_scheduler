#!/usr/bin/env python3
import os
import shutil
import subprocess
import tempfile
import time
import yaml
from jinja2 import Environment, FileSystemLoader

def available_hosts():
    """
    Returns list of available hosts from `hosts.txt`
    """
    with open('hosts.txt', 'r') as f:
        hosts = f.read().splitlines()
    assert len(hosts) > 0
    return hosts

def remote_check_exists(hosts, abs_path):
    """
    Returns whether a file/dir exists at abs_path on any of hosts
    """
    cmd = f"""
        test -e {abs_path}
    """
    return run_parallel_command(hosts, 'parallel-ssh', cmd)
    

def remote_clean(hosts, abs_path):
    """
    Deletes folder and waits for them all to be deleted
    """
    # Delete folders
    cmd = f"""
        rm -rf {abs_path}
    """
    run_parallel_command(hosts, 'parallel-ssh', cmd)

    # Wait for cleanup to finish
    ticks = 0
    cmd = f"""
        test -e {abs_path}
    """
    while remote_check_exists(hosts, abs_path): # wait until command fails == directories are deleted
        ticks += 1
        print("Deleting" + ((ticks % 4) * "."), end='\r')
        time.sleep(5)
    print(f'{abs_path} has been successfully deleted')

def cleanup(path):
    """
    Uses relative path from the `my_scheduler` folder
    """
    try:
        cwd = os.path.dirname(__file__)
        cleaned_path = os.path.join(cwd, path)
        shutil.rmtree(cleaned_path)
    except FileNotFoundError as not_found:
        print(f"no such file : {not_found.filename}")

def fill_template(filepath, config):
    DIR_PATH = os.path.dirname(os.path.realpath(filepath))
    basename = os.path.basename(os.path.realpath(filepath))
    env = Environment(loader=FileSystemLoader(DIR_PATH))
    template = env.get_template(basename)
    template = template.render(**config)
    return template

def load_config():
    """
    Loads in variables declared in `config.yaml` and `template.yaml`
    """
    # load the config
    config_file = os.path.join('config.yaml')
    config = yaml.safe_load(open(config_file, 'r'))
    # template the rest
    template = fill_template('template.yaml', config)
    template = yaml.safe_load(template)
    return {**config, **template} # merge key-set

def run_enum_command(hosts, cmd, stdout=None, stderr=None):
    """
    Runs command across hosts. Expects cmd to be a formatted string with a single argument
    to be an unsigned integer assigned to each host i.e. `cmd` is:

    "python -m torch.distributed.launch --nproc_per_node 8 --node_number {} <YOUR_SCRIPT.py>"
    """
    for i, host in enumerate(hosts):
        cmd = cmd.format(i)
        cmd = cmd.split()
        try:
            print('{}::{}'.format(subprocess.check_output(['ssh', host] + cmd).decode('utf-8').strip(), cmd))
        except subprocess.CalledProcessError as e:
            print('{}::{}'.format(e.output.decode('utf-8').strip(), cmd))

def run_parallel_command(hosts, pcmd, cmd, block=True, stdout=None, stderr=None):
    """
    Runs `cmd` across multiple different hosts using parallel-ssh. If block=True,
    output is True or False depending on whether all commands were returned success
    across all hosts.
    If block=False
    """
    assert pcmd in ['parallel-ssh', 'parallel-rsync', 'parallel-scp']
    with tempfile.NamedTemporaryFile(mode='w') as f:
        f.write('\n'.join(hosts) + '\n')
        f.flush()
        pssh_args = ['-h', f.name]
        if stdout: pssh_args += ['-o', stdout]
        if stderr: pssh_args += ['-e', stderr]
        pssh_args += cmd.split()
        try:
            if block: 
                print('{}::{} {}'.format(subprocess.check_output([pcmd] + pssh_args).decode('utf-8').strip(), pcmd, cmd))
                return True
            else:
                p = subprocess.Popen([pcmd] + pssh_args)
                time.sleep(5) # give forked processes enough time to read host list
                return p
        except subprocess.CalledProcessError as e:
            print('{}::{} {}'.format(e.output.decode('utf-8').strip(), pcmd, cmd))
            return False

def parallel_rsync(hosts, src, dst, **kwargs):
    """
    Runs copies to hosts from src to dst using parallel-rsync
    """
    cmd = """
        {} {} {} {}
    """.format(config['rsync_flags'], f"--par {len(hosts)}",
                src, dst)
    p = run_parallel_command(hosts, 'parallel-rsync', cmd, block=False, **kwargs)
    return p

def parallel_scp(hosts, src, dst, **kwargs):
    """
    Runs copies to hosts from src to dst using parallel-scp
    """
    cmd = f"{src} {dst}"
    run_parallel_command(hosts, 'parallel-scp', cmd, **kwargs)

def setup_logging(logdir):
    """
    creates directories for logging stdout and stderr and returns the paths for both
    upon success
    """
    cwd = os.path.dirname(__file__)
    sync_out = os.path.join(cwd, f'{logdir}/out')
    sync_err = os.path.join(cwd, f'{logdir}/err')
    os.makedirs(sync_out, exist_ok=True)
    os.makedirs(sync_err, exist_ok=True)
    return sync_out, sync_err

config = load_config()
hosts = available_hosts()
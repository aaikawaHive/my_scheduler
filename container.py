import argparse
import os
import sys
import tempfile
from utils import config, hosts, run_parallel_command, run_enum_command, setup_logging, parallel_scp, fill_template

logdir = 'container/'

def up(args):
    # copy install script to home directory
    stdout, stderr = args.stdout, args.stderr
    USER, src = config['user'], config['install_script']
    install_cmd = fill_template(src, config)
    install_basename = os.path.basename(src)
    dst = f"/home/{USER}/{install_basename}"
    with tempfile.NamedTemporaryFile('w') as f:
        f.write(install_cmd)
        f.flush()
        src = f.name
        parallel_scp(hosts, src, dst, stdout=stdout, stderr=stderr)
    # bring up docker container and install requirements by launching the install script
    cmd = f"""
        {args.inline} -t 0 {config['docker_start']} && sudo chmod +x {dst}
    """
    run_parallel_command(hosts, 'parallel-ssh', cmd, stdout=stdout, stderr=stderr)
    cmd = f"""
        {args.inline} -t 0 sudo docker exec {USER}_spawn {dst}
    """
    run_parallel_command(hosts, 'parallel-ssh', cmd, stdout=stdout, stderr=stderr)
    return 0

def exec(args):
    # copy exec script to home directory
    stdout, stderr = args.stdout, args.stderr
    USER, src = config['user'], config['exec_script']
    exec_basename = os.path.basename(src)
    exec_cmd = fill_template(src, config)
    dst = f"/home/{USER}/{exec_basename}"
    with tempfile.NamedTemporaryFile('w') as f:
        f.write(exec_cmd)
        f.flush()
        src = f.name
        parallel_scp(hosts, src, dst, stdout=stdout, stderr=stderr)
    # execute on docker container
    
    if args.enum: 
        cmd = f"""sudo chmod +x {dst} && sudo docker exec {USER}_spawn {dst}""" + " {} {} "
        cmd = f""" "{cmd}" """
        run_enum_command(hosts, cmd, stdout=stdout, stderr=stderr)
    else:
        cmd = f"""
        {args.inline} -t 0 sudo chmod +x {dst} && sudo docker exec {USER}_spawn {dst}
        """
        run_parallel_command(hosts, 'parallel-ssh', cmd, stdout=stdout, stderr=stderr)
    return 0

def down(args):
    stdout, stderr = args.stdout, args.stderr
    USER, src = config['user'], config['clean_script']
    clean_basename = os.path.basename(src)
    clean_cmd = fill_template(src, config)
    dst = f"/home/{USER}/{clean_basename}"
    with tempfile.NamedTemporaryFile('w') as f:
        f.write(clean_cmd)
        f.flush()
        src = f.name
        parallel_scp(hosts, src, dst, stdout=stdout, stderr=stderr)
    cmd = f"""
        {args.inline} {dst} && sudo docker stop {USER}_spawn && sudo docker rm {USER}_spawn
    """
    run_parallel_command(hosts, 'parallel-ssh', cmd, stdout=stdout, stderr=stderr)
    return 0

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="""
        Utility for building docker container for creating/removing docker containers with installed requirements
        """,
    )

    parser.add_argument('--save_logs', action='store_true',
                         help='save stdout and stderr from hosts')

    parser.add_argument('--inline', action='store_true',
                         help='print stdout to inline')
    
    subparsers = parser.add_subparsers(dest='command', help='command to run')
    subparsers.required = True

    parser_up = subparsers.add_parser(
        'up',
        help=r'creates the docker container `${user}_spawn` and runs the specified install script on the hosts',
    )
    parser_up.set_defaults(func=up)
    parser_exec = subparsers.add_parser(
        'exec',
        help=r'runs execute script in the docker container `${user}_spawn`',
    )
    parser_exec.add_argument('--enum', action='store_true',
                             help='run with formatted index included')
    parser_exec.set_defaults(func=exec)
    parser_down = subparsers.add_parser(
        'down',
        help=r'removes the docker container `${user}_spawn`',
    )
    parser_down.set_defaults(func=down)

    args = parser.parse_args(argv)
    if args.save_logs:
        args.stdout, args.stderr = setup_logging(logdir)
    else:
        args.stdout, args.stderr = None, None
    args.inline = '-i' if args.inline else ''
    return args.func(args)

if __name__ == '__main__':
    sys.exit(main())
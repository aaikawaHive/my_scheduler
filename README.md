This project contains some commands that'll be useful for setting up distributed tasks (i.e. training, ffmpeg on multiple nodes). You'll want to start off in a docker container and install `pssh`

```
bash start_docker.sh
```
# Host Selection
So you don't have to keep typing so much, I would alias your parallel commands for quick parallel debugging
```
# add to ~/.bashrc
alias pssh=parallel-ssh -h /persist/${USER}/my_scheduler/hosts.txt
alias pscp=parallel-scp -h /persist/${USER}/my_scheduler/hosts.txt
alias prsync=parallel-rsync -h /persist/${USER}/my_scheduler/hosts.txt
```

You'll need to pick the list of hosts you want to use. Either manually specify in `hosts.txt` or specify what resources you need (i.e. number of nodes, amount of disk, {80GB, 40GB, 10GB} machines) and automatically selecting machines with the `config.yaml` and running `hosts.py`

```
# change your config, values automatically populate fields in `template.yaml`
vim config.yaml

# find a list of open hosts
python hosts.py
```

# Code/Data Sync

Now that your hosts are specified start copying your files and data over.
TODO : handle data splitting (i.e. each host has a different set of data), by default every machine has the same data


```
# specify project and data filepaths. copies to /home/{{ user }} by default. should probably change
vim config.yaml

# copy project folder
python sync.py project

# copy data folder
python sync.py data
```

# Container setup

`container.py` contains utilities for spinning up containers and executing code from them.

Get your worker nodes setup by first specifying your `scripts/install.sh` file and your docker up command in `template.yaml`.  These should ideally install all the requirements for whatever your code is. 

```
# creates container, copies `scripts/install.sh` and runs `scripts/install.sh` to install requirements
python container.py up
```

Execute your code in parallel. Oftentimes we need to know the total number of nodes participating in a job. `container.py` handles that and formats the command for you.

```
# creates `exec.sh` which has the formatted bash command for execution
python container.py exec --enum

# run the parallel launcher in `exec.sh`
bash exec.sh
```

If for any reason you want to delete the containers on the hosts

```
# remove using `container.py`
python container.py down

# using pssh
pssh sudo docker stop {username}_spawn
pssh sudo docker rm {username}_spawn
```

# Tips

`pssh` has the ability to print the output of from each host using the `--inline` flag.  This is useful for debugging. Many of the scripts in `sync.py` also have this flag so you can debug as you run.

```
# pssh with output
pssh --inline echo 'hello'

# run container.py and see the output of the install
python container.py --inline up
```

Oftentimes you will need to kill hanging processes when one node fails and causes the others to wait. Usually pkill will suffice.

```
# end all python processes
pssh pkill python
```
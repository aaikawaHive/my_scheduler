sudo nvidia-docker run --name ${USER} --privileged -it --network=host --ipc=host -v /persist/${USER}/.aws:/root/.aws -v /root/.ssh:/root/.ssh -v /persist/${USER}:/persist/${USER} -v /home/${USER}:/home/${USER} nvcr.io/nvidia/pytorch:21.06-py3
apt update
apt install -y pssh
cd /persist/${USER}/my_scheduler
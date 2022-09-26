from utils import hosts
import subprocess
import tempfile

done = set()

with tempfile.TemporaryDirectory(dir='./') as d:
    for i, h in enumerate(hosts):
        try:
            print(h)
            cmd = f"scp {h}:/home/aaikawa/done.txt {d}/"
            print(subprocess.check_output(cmd, shell=True).decode('utf-8').strip())
            with open(f'{d}/done.txt', 'r') as f:
                completed = set(f.read().split())
                done = done.union(completed)
        except:
            continue

done = sorted(list(done))
with open('done.txt', 'w') as f:
    f.write('\n'.join(done))
print('# done = ', len(done))

for i, h in enumerate(hosts):
    print(h)
    cmd = f"scp done.txt {h}:/home/aaikawa/done.txt"
    print(subprocess.check_output(cmd, shell=True).decode('utf-8').strip())
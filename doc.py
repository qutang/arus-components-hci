import subprocess
import shutil
import os

print('remove old')
shutil.rmtree('./docs', ignore_errors=True)

print('building documentations')
# build docs
subprocess.run("pdoc --html -o docs arus_components_hci -f --template-dir templates",
               shell=True)

# move docs
items = os.listdir('./docs/arus_components_hci/')
for item in items:
    source = os.path.join('./docs/arus_components_hci/', item)
    target = os.path.join('./docs', item)
    if os.path.isdir(source):
        shutil.copytree(source,
                        target)
        shutil.rmtree(source, ignore_errors=True)
    else:
        shutil.copyfile(source, target)
        os.remove(source)
os.removedirs('./docs/arus_components_hci/')

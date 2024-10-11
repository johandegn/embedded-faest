#!/usr/bin/env python3
# This script uses the prepare_nist.py script to export the
# specified implementation to the pqm4 project.
import os
import sys
import subprocess
import shutil
from pathlib import Path

TARGET_DIR = "target"


all = ['faest_128f', 'faest_128s', 'faest_192f', 'faest_192s', 'faest_256f', 'faest_256s',\
        'faest_em_128f', 'faest_em_128s', 'faest_em_192f', 'faest_em_192s', 'faest_em_256f', 'faest_em_256s']


def prepare_single(name: str):
    print(f"Preparing {name}")
    cmd = ["python3",
           "faest/tools/prepare_nist.py",
           "faest",
           "faest/build",
           TARGET_DIR,
           name]
    r = subprocess.run(cmd, text=True)
    if r.returncode != 0:
        exit(1)


def prepare_all():
    for e in all:
        prepare_single(e)


def move_single_to_pqm4(name: str):
    folder = f"pqm4/crypto_sign/{name}/ref"

    # Remove existing folder with content
    try:
        shutil.rmtree(folder)
    except FileNotFoundError:
        pass

    # Copy to folder
    shutil.copytree(f"target/Reference_Implementation/{name}", folder)

    # Make config.h in folder
    with open(f"{folder}/config.h", "w") as f:
        f.write(f"#define HAVE_RANDOMBYTES\n")
        f.write(f"#define PQCLEAN\n")

    # move content of sha3 out while merging config.h
    project_root = Path(folder)
    sha3_sources = project_root / "sha3"
    for source in sha3_sources.glob("*"):
        if "config.h" in source.as_posix():
            with open(f"{folder}/sha3/config.h", "r") as f:
                conf = f.read()
            with open(f"{folder}/config.h", "a") as f:
                f.write("\n")
                f.write(conf)
        else:
            shutil.move(source, project_root)
    shutil.rmtree(sha3_sources)
    
    # Prepend '#include "config.h"' to aes.c, randomness.c and hash_shake.h
    with open(f"{folder}/aes.c", "r") as f:
        data = f.read()
    with open(f"{folder}/aes.c", "w") as f:
        f.write('#include "config.h"\n')
        f.write(data)
    with open(f"{folder}/randomness.c", "r") as f:
        data = f.read()
    with open(f"{folder}/randomness.c", "w") as f:
        f.write('#include "config.h"\n')
        f.write(data)
    with open(f"{folder}/hash_shake.h", "r") as f:
        data = f.read()
    with open(f"{folder}/hash_shake.h", "w") as f:
        f.write('#include "config.h"\n')
        f.write(data)




def move_all_to_pqm4():
    for e in all:
        move_single_to_pqm4(e)


if __name__ == '__main__':
    # Create target dir for temporary files
    os.makedirs(TARGET_DIR, exist_ok=True)

    # Prepare files
    if len(sys.argv) == 1:
        prepare_all()
        move_all_to_pqm4()
    elif len(sys.argv) == 2:
        name = sys.argv[1]
        prepare_single(name)
        move_single_to_pqm4(name)
    
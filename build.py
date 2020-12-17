"""
Place this script in the root of KSAM assets and then run it to build.

Usage: python3 build.py [dest location]
"""

import sys
import shutil
import util.mtxtool as mtx
import configparser as cp

config = cp.ConfigParser()

def loadConfig(name):
    config.read()

def main(dest):
    shutil.copytree("./assets", dest + "/assets", dirs_exist_ok = True);

    for i in pngfiles:
        mtx.bakeMtxFromPng(filein, fileout);
    


if (__name__ == "__main__"):
    dirname = sys.argv[0];
    main(dirname);

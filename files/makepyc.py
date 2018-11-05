#!/usr/bin/env python

import compileall
import sys

from os import unlink, walk
from os.path import exists, join, splitext


assert sys.argv[1], "usage: makepyc /path/to/lib"


for root, dirs, files in walk(sys.argv[1]):
    for name in files:
        if name.endswith('.pyc'):
            pyc = join(root, name)
            py = splitext(pyc)[0] + '.py'
            if not exists(py):
                print('Removing orphaned', pyc, '...')
                unlink(pyc)

compileall.compile_dir(sys.argv[1])

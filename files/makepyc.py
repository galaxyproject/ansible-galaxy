#!/usr/bin/env python

import sys
import compileall

from os import walk, unlink
from os.path import join, splitext, exists


assert sys.argv[1], "usage: makepyc /path/to/lib"


for root, dirs, files in walk(sys.argv[1]):
    for name in files:
        if name.endswith('.pyc'):
            pyc = join(root, name)
            py = splitext(pyc)[0] + '.py'
            if not exists(py):
                print 'Removing orphaned', pyc, '...'
                unlink(pyc)

compileall.compile_dir(sys.argv[1])

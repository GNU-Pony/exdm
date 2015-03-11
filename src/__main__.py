#!/usr/bin/env python3
copyright = '''
exdm – The Extensible X Display Manager

Copyright © 2015  Mattias Andrée (maandree@member.fsf.org)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import os, sys

from argparser import *

from util import *
from misc import *
from xauth import *
from xserver import *



PROGRAM_NAME = 'exdm' # @@
'''
:str  The name of the program
'''

PROGRAM_VERSION = '0' # @@
'''
:str  The version of the program
'''




# Set process title
setproctitle(sys.argv[0])


# Read command line arguments
parser = ArgParser('The Extensible X Display Manager',
                   sys.argv[0] + ' [vt$VT] [VARIABLE=VALUE]... [OPTION]...',
                   None, None, True, None)

parser.add_argumented(  ['-c', '--configurations'],         0, 'FILE', 'Select configuration file')
parser.add_argumented(  ['-x', '--x-argument'],             0, 'ARG',  'Pass an argument on to the X server')
parser.add_argumentless(['-h', '-?', '--help'],             0,         'Print this help information')
parser.add_argumentless(['-C', '--copying', '--copyright'], 0,         'Print copyright information')
parser.add_argumentless(['-W', '--warranty'],               0,         'Print non-warranty information')
parser.add_argumentless(['-v', '--version'],                0,         'Print program name and version')

parser.parse()
parser.support_alternatives()

# Check for no-action options
if parser.opts['--help'] is not None:
    parser.help()
    sys.exit(0)
elif parser.opts['--copyright'] is not None:
    print(copyright[1 : -1])
    sys.exit(0)
elif parser.opts['--warranty'] is not None:
    print(copyright.split('\n\n')[3])
    sys.exit(0)
elif parser.opts['--version'] is not None:
    print('%s %s' % (PROGRAM_NAME, PROGRAM_VERSION))
    sys.exit(0)



# Check that the user is root
check_root_uid()

# Configure signal
configure_signals(lambda sig, frame : sys.exit(1)) # TODO stop server

# Set environment
set_environment_from_cmdline(parser)

# Get virtual terminal
get_virtual_terminal(parser)

# Get display
if get_display() is None:
    sys.exit(1)



# [X is running] ||
server_pid = fork_exec_xserver(parser)
if timedwaitpid(server_pid, 0) is None:
    if not connect(): # TODO
        stop_server() # TODO
        print('%s: unable to connect to X server' % sys.argv[0], file = sys.stderr)
        sys.exit(1)


# Remove server authentication
remove_authentication_file()


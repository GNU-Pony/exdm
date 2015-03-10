#!/usr/bin/env python3
'''
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

import os
import sys
import random
from subprocess import Popen, PIPE



RUNDIR = '/run' # @@
'''
:str  The installed system's path for /run
'''

PKGNAME = 'exdm' # @@
'''
:str  The name of the page as installed
'''



# Test that the user is root
if not os.getuid() == 0:
    print('%s: this program can only be ran by root' % sys.argv[0], file = sys.stderr)
    sys.exit(1)


# Get virtual terminal
def is_numeral(text : str) -> bool:
    try:
        int(text)
        return True
    except:
        return False
vt = [int(a[2:]) for a in sys.argv[1:] if a.startswith('vt') and is_numeral(a[2:])]
vt = [a for a in vt if 0 < a < 64]
if len(vt) == 1:
    [vt] = vt
else:
    proc = Popen(['fgconsole', '--next-available'], stdin = sys.stdin, sysout = PIPE)
    vt = int(proc.communicate()[0].decode('utf-8', 'strict').strip())
print('%s: opening exdm on vt%i' % (sys.argv[0], vt), file = sys.stderr)


# Get hostname
command = ['hostname']
if os.uname().sysname.startswith('Linux'):
    proc = Popen(command + ['--version'], stdout = PIPE, stderr = PIPE)
    out, err = proc.communicate()
    if 'GNU' not in (out + err):
        command.append('-f')
proc = Popen(command, stdout = PIPE, stderr = sys.stderr)
hostname = proc.communicate()[0]


# Create server authentication cookie
authfile = '%s/%s.vt%i.auth' % (rundir, pkgname, vt)
if os.path.exists(authfile):
    with open(authfile, 'rb') as file:
        mit_cookie = file.read().decode('utf-8', 'strict').strip()
else:
    digits = '0123456789abcedf'
    mit_cookie = ''.join(digits[random.randint(0, 15)] for i in range(64))
os.environ['XAUTHORITY'] = authfile
os.putenv('XAUTHORITY', os.environ['XAUTHORITY']) # just to be on the safe side


# Get X display index
command = 'xauth list | grep "^%s/unix:" | grep "[[:space:]]%s$" | cut -f 1 | cut -d ' ' -f 1 | sed 1q'
command %= (hostname, mit_cookie)
command = ['sh', '-c', command]
proc = Popen(command, stdout = PIPE, stderr = sys.stderr)
display = proc.communicate()[0].decode('utf-8', 'strict').strip()
if len(display) == 0:
    display = 0
else:
    display = int(display.split(':')[-1])

# Create server authentication file
while display < 256:
    # Attempt to create authentication file
    proc = Popen(['xauth', '-f', authfile, '-q'], stdin = PIPE, stdout = sys.stdout, stderr = sys.stderr)
    proc.stdin.write(('add :%i . %s\n' % (display, mit_cookie)).encode('utf-8'))
    proc.stdin.write(('exit %s\n').encode('utf-8'))
    proc.wait()
    
    # Test that we were successful
    command = 'xauth list | sed -n "s/^%s\/unix:%i[[:space:]*].*[[:space:]*]//p"'
    command = ['sh', '-c', command % (hostname, display)]
    proc = Popen(command, stdout = PIPE, stderr = sys.stderr)
    test_cookie = proc.communicate()[0].decode('utf-8', 'strict').strip()
    if test_cookie == mit_cookie:
        break
    else:
        display += 1
if display == 256:
    print('%s: fail to find an unused display, stopped at 256' % sys.argv[0], file = sys.stderr)
    sys.exit(1)

# Convert `display` to a $DISPLAY string
display = ':%i' % display





# Remove server authentication
proc = Popen(['xauth', '-f', authfile, '-q'], stdin = PIPE, stdout = sys.stdout, stderr = sys.stderr)
proc.stdin.write(('remove %s\n' % display).encode('utf-8'))
proc.stdin.write(('exit %s\n').encode('utf-8'))
proc.wait()
try:
    os.unlink(authfile)
except:
    pass


# sessreg


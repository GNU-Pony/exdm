# -*- python -*-
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


RUNDIR = '/run' # @@
'''
:str  The installed system's path for /run
'''

PKGNAME = 'exdm' # @@
'''
:str  The name of the page as installed
'''



def generate_mit_cookie() -> str:
    '''
    Generate MIT-MAGIC-COOKIE-1 key for X server authentication
    
    @return  :str  The generated cookie, it is 32 digits lowercase hexadecimal
    '''
    import random
    return ''.join('0123456789abcedf'[random.randint(0, 15)] for i in range(32))


def get_display_with_cookie(mit_cookie : str, default_display = None) -> int:
    '''
    Get the index of the display that uses a known cookie
    
    @param   mit_cookie:str          The cookie that the display should have
    @param   default_display         The value that should be returned if no display can be found
    @return  :int|`default_display`  The display that uses the cookie
    '''
    import sys
    from subprocess import Popen, PIPE
    from util import get_hostname
    command = 'xauth list | grep "^%s/unix:" | grep "[[:space:]]%s$" | cut -f 1 | cut -d ' ' -f 1 | sed 1q'
    command %= (get_hostname(), mit_cookie)
    command = ['sh', '-c', command]
    proc = Popen(command, stdout = PIPE, stderr = sys.stderr)
    display = proc.communicate()[0].decode('utf-8', 'strict').strip()
    if len(display) == 0:
        display = default_display
    else:
        display = int(display.split(':')[-1])
    return display


def create_authentication_file(authfile : str, display : int, mit_cookie : str) -> bool:
    '''
    Try to create an authentication file
    
    @param   authfile:str    The authentication file's pathname
    @param   display:int     The index of the X display
    @param   mit_cookie:str  The cookie for the display
    @return  :bool           Whether the attempt was successful
    '''
    import sys
    from subprocess import Popen, PIPE
    from util import get_hostname
    
    # Attempt to create authentication file
    proc = Popen(['xauth', '-f', authfile, '-q'], stdin = PIPE, stdout = sys.stdout, stderr = sys.stderr)
    proc.stdin.write(('add :%i . %s\n' % (display, mit_cookie)).encode('utf-8'))
    proc.stdin.write(('exit %s\n').encode('utf-8'))
    proc.wait()
    
    # Test that we were successful
    command = 'xauth list | sed -n "s/^%s\/unix:%i[[:space:]*].*[[:space:]*]//p"'
    command = ['sh', '-c', command % (get_hostname(), display)]
    proc = Popen(command, stdout = PIPE, stderr = sys.stderr)
    test_cookie = proc.communicate()[0].decode('utf-8', 'strict').strip()
    return test_cookie == mit_cookie


def remove_authentication_file():
    '''
    Remove server authentication
    
    The environment variables XAUTHORITY and DISPLAY must be set
    '''
    import os, sys
    from subprocess import Popen, PIPE
    authfile = os.environ['XAUTHORITY']
    proc = Popen(['xauth', '-f', authfile, '-q'], stdin = PIPE, stdout = sys.stdout, stderr = sys.stderr)
    proc.stdin.write(('remove %s\n' % os.environ['DISPLAY']).encode('utf-8'))
    proc.stdin.write(('exit %s\n').encode('utf-8'))
    proc.wait()
    try:
        os.unlink(authfile)
    except:
        pass
    try:
        os.unlink(authfile + '.raw')
    except:
        pass


def get_display() -> str:
    '''
    Select display, create cookie and create authentication file
    
    This function will set the environent variables XAUTHORITY and DISPLAY
    
    @return  :mit_cookie:str?  The cookie, `None` on failure
    '''
    import os
    from util import setenv
    from misc import get_mit_cookie
    
    # Get and export authentication file
    authfile = '%s/%s.vt%s.auth' % (RUNDIR, PKGNAME, os.environ['XDG_VTNR'])
    setenv('XAUTHORITY', authfile)
    
    # Get cookie
    mit_cookie = get_mit_cookie(authfile)
    
    # Store authentication cookie
    with open(authfile + '.raw', 'wb', opener = lambda p, f : os.open(p, f, mode = 0o600)) as file:
        file.write(mit_cookie.encode('utf-8'))
    
    # Get preliminary X display index
    display = get_display_with_cookie(mit_cookie, 0)
    
    # Create server authentication file
    while display < 256:
        if create_authentication_file(authfile, display, mit_cookie):
            break
        else:
            display += 1
    if display == 256:
        print('%s: fail to find an unused display, stopped at 256' % sys.argv[0], file = sys.stderr)
        return (None, mit_cookie)
    
    # Export $DISPLAY
    setenv('DISPLAY', ':%i' % display)
    
    return mit_cookie


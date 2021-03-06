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


PROGRAM_NAME = 'exdm' # @@
'''
:str  The name of the program
'''



def set_environment_from_cmdline(cmdline):
    '''
    Set up environment variables according to the command line
    
    @param  cmdline:ArgParser  The command line parser
    '''
    from util import setenv
    for var, val in [(a.split('=')[0], '='.join(a.split('=')[1:])) for a in cmdline.files if '=' in a]:
        setenv(var, val)


def get_virtual_terminal(cmdline) -> int:
    '''
    Get which virtual terminal the X servers should use
    
    This function will set the environment variable XDG_VTNR
    
    @param   cmdline:ArgParser  The command line parser
    @return  :int               The virtual terminal the X servers should use
    '''
    import sys
    from subprocess import Popen, PIPE
    from util import setenv
    vt = [int(a[2:]) for a in cmdline.files if a.startswith('vt') and is_numeral(a[2:])]
    vt = [a for a in vt if 0 < a < 64]
    if len(vt) == 1:
        [vt] = vt
    else:
        proc = Popen(['fgconsole', '--next-available'], stdin = sys.stdin, sysout = PIPE)
        vt = int(proc.communicate()[0].decode('utf-8', 'strict').strip())
    setenv('XDG_VTNR', str(vt))
    print('%s: opening %s on vt%i' % (sys.argv[0], PROGRAM_NAME, vt), file = sys.stderr)
    return vt


def check_root_uid():
    '''
    Halt if the user is not root
    '''
    import os, sys
    if not os.getuid() == 0:
        print('%s: this program can only be run by root' % sys.argv[0], file = sys.stderr)
        sys.exit(1)


def get_mit_cookie(authfile : str) -> str:
    '''
    Read an existing or generate a new cookie for X server authentication
    
    @param   authfile:str  The pathname of the file where the cookie might be stored
    @return  :str          The cookie, it is 32 digits lowercase hexadecimal
    '''
    import os
    from xauth import generate_mit_cookie
    if os.path.exists(authfile + '.raw'):
        # Incase the program crashed and was respawned
        with open(authfile + '.raw', 'rb') as file:
            mit_cookie = file.read().decode('utf-8', 'strict').strip()
    else:
        mit_cookie = generate_mit_cookie()
    return mit_cookie


def configure_signals(signal_handler : callable):
    '''
    Configure signals
    
    @param  signal_handler:(signal:int, stack)→void  Function to call when the display
                                                     manager should exit because of a signal
    '''
    import signal
    def signal_do_nothing(signal, stack):
        signal.signal(signal.SIGUSR1, signal_do_nothing)
    signal.signal(signal.SIGQUIT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGKILL, signal_handler)
    signal.signal(signal.SIGINT,  signal_handler)
    signal.signal(signal.SIGHUP,  signal_handler)
    signal.signal(signal.SIGPIPE, signal_handler)
    signal.signal(signal.SIGUSR1, signal_do_nothing)


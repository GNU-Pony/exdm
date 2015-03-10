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


def get_xserver_arguments(cmdline) -> list:
    '''
    Get the arguments that are executed to start the X server
    
    The environment variables DISPLAY, XDG_VTNR and XAUTHORITY must be set
    
    @param   cmdline:ArgParser  The command line parser
    @return  :list<str>         The arguments that are executed to start the X server
    '''
    import os
    server_args = ['X',     os.environ['DISPLAY'],
                   'vt%s' % os.environ['XDG_VTNR'],
                   '-auth', os.environ['XAUTHORITY']]
    server_args += [a for a in cmdline.opts['--x-argument'] if a is not None]
    return server_args


def ignore_signals_for_xserver():
    '''
    Configure signals to be ignored for the X server
    '''
    import signal
    signal.signal(signal.SIGTTIN, signal.SIG_IGN)
    signal.signal(signal.SIGTTOU, signal.SIG_IGN)
    signal.signal(signal.SIGUSR1, signal.SIG_IGN)


def fork_exec_xserver(cmdline) -> int:
    '''
    Fork–exec the X server
    
    @param   cmdline:ArgParser  The command line parser
    @return  :int               The process Id of the X server
    '''
    import os, sys
    server_args = get_xserver_arguments(cmdline)
    server_pid = os.fork()
    if server_pid == 0:
        ignore_signals_for_xserver()
        os.setpgid(0, os.getpid())
        try:
            os.execvp(server_args[0], server_args)
        except:
            pass
        print('%s: failed to start X server' % sys.argv[0], file = sys.stderr)
        sys.exit(1)
    return server_pid


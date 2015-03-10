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


def setproctitle(title : str):
    '''
    Set process title
    
    @param  title:str  The title of the process
    '''
    import ctypes, sys
    try:
        # Remove path, keep only the file,
        # otherwise we get really bad effects, namely
        # the name title is truncates by the number
        # of slashes in the title. At least that is
        # the observed behaviour when using procps-ng.
        title = title.split('/')[-1]
        # Create strng buffer with title
        title = title.encode(sys.getdefaultencoding(), 'replace')
        title = ctypes.create_string_buffer(title)
        if 'linux' in sys.platform:
            # Set process title on Linux
            libc = ctypes.cdll.LoadLibrary('libc.so.6')
            libc.prctl(15, ctypes.byref(title), 0, 0, 0)
        elif 'bsd' in sys.platform:
            # Set process title on at least FreeBSD
            libc = ctypes.cdll.LoadLibrary('libc.so.7')
            libc.setproctitle(ctypes.create_string_buffer(b'-%s'), title)
    except:
        pass


def setenv(variable : str, value : str):
    '''
    Set an environment variable
    
    @param  variable:str  The variable's name
    @param  value:str?    The variable's new value, `None` to delete it
    '''
    import os
    if value is not None:
        os.environ[variable] = value
        os.putenv(variable, value) # just to be on the safe side
    else:
        del os.environ[variable]
        os.unsetenv(variable) # just to be on the safe side


def is_numeral(text : str) -> bool:
    '''
    Test if a string is numeral
    
    @param   text:str  The string
    @return  :bool     Whether the string is numeral
    '''
    try:
        int(text)
        return True
    except:
        return False


__util_hostname = None
def get_hostname() -> str:
    '''
    Get the computer's hostname
    
    @return  :str  The computer's hostname
    '''
    global __util_hostname
    if __util_hostname is not None:
        return __util_hostname
    else:
        import os, sys
        from subprocess import Popen, PIPE
        command = ['hostname']
        if os.uname().sysname.startswith('Linux'):
            proc = Popen(command + ['--version'], stdout = PIPE, stderr = PIPE)
            out, err = proc.communicate()
            if 'GNU' not in (out + err):
                command.append('-f')
        proc = Popen(command, stdout = PIPE, stderr = sys.stderr)
        hostname = proc.communicate()[0].strip()
        __util_hostname = hostname
        return hostname


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
from subprocess import Popen, PIPE


SYSCONFDIR = '/etc'
'''
:str  The installed system's path for /etc
'''

ISSUE_FILE = SYSCONFDIR + '/issue'
'''
:str  The pathname of the issue file
'''

DEFAULT_ISSUE_FILE = ISSUE_FILE + '.default'
'''
:str  The pathname of the default issue file
'''


class Issue:
    '''
    /etc/issue support
    
    @variable  exists:bool          Whether the issue file exists
    @variable  default_exists:bool  Whether the default issue file exists
    @variable  is_default:bool      Whether the issue file is identical to the default issue file
    @variable  issue:str?           The issue file, parsed, `None` if it does not exist
    '''
    
    def __init__(self):
        '''
        Constructor
        '''
        self.exists         = os.path.exists(ISSUE_FILE)
        self.default_exists = os.path.exists(DEFAULT_ISSUE_FILE)
        
        if not self.exists:
            self.is_default = not self.default_exists
            self.issue = None
        
        with open(ISSUE_FILE, 'rb') as file:
            issue_data = file.read()
        
        if self.default_exists:
            with open(DEFAULT_ISSUE_FILE, 'rb') as file:
                default_issue_data = file.read()
            self.is_default = issue_data == default_issue_data
            del default_issue_data
        else:
            self.is_default = False
        
        issue_data = issue_data.decode('utf-8', 'strict')
        
        def sh(command):
            p = ['sh', '-c', command]
            p = Popen(p, stdin = sys.stdin, stdout = PIPE, stderr = sys.stderr)
            p = p.communicate()[0].decode('utf-8', 'replace')
            return p.rstrip('\n')
        buf = ''
        esc = False
        inet = lambda ip, face = '' : sh("ifconfig %s | grep '^ *%s ' | grep -Po '%s [^ ]*' | cut -d ' ' -f 2 | sed 1q" % (face, ip, ip))
        uname = os.uname()
        for i in range(len(issue_data)):
            c = issue_data[i]
            i += 1
            d = '\n' if i == len(issue_data) else issue_data[i]
            def get_arg():
                arg = ''
                for j in range(i, len(issue_data)):
                    arg += issue_data[j]
                    if arg[-1] == '}':
                        return arg[1 : -1]
                return ''
            if esc:
                esc = False
                if  c in 'eE':  buf += '\033'
                elif c == 'N':  buf += '\n'
                elif c == 'T':  buf += '\t'
                elif c == 's':  buf += uname.sysname
                elif c == 'n':  buf += uname.nodename
                elif c == 'r':  buf += uname.release
                elif c == 'v':  buf += uname.version
                elif c == 'm':  buf += uname.machine
                elif c == 'o':  buf += sh('hostname -y')
                elif c == 'O':  buf += sh('hostname -d')
                elif c == 'd':  buf += sh('date +%Y-%m-%d')
                elif c == 't':  buf += sh('date +%H:%M:%S')
                elif c == 'l':  buf += os.ttyname(2).split('/')[-1]
                elif c == 'b':  buf += sh("stty | grep -Po 'speed [^ ]* baud;' | cut -d ' ' -f 2")
                elif c == 'u':  buf += sh('who | wc -l')
                elif c == 'U':  n = sh('who | wc -l') ; buf += n + (' user' if n == '1' else ' users')
                elif c == '4':  buf += inet('inet', get_arg() if d == '{' else '')
                elif c == '6':  buf += inet('inet6', get_arg() if d == '{' else '')
                elif c == 'S':
                    if os.path.exists(SYSCONFDIR + '/os-release'):
                        arg = get_arg() if d == '{' else ''
                        if arg == '':
                            arg = 'PRETTY_NAME'
                        val = sh('. %s/os-release ; echo "${%s}"' % (SYSCONFDIR, arg))
                        if (arg == 'PRETTY_NAME') and (val == ''):
                            val = uname.sysname
                        elif arg == 'ANSI_COLOR':
                            val = '\033[%sm' % val
                        buf += val
            elif c == '\\':
                esc = True
            else:
                buf += c
        
        self.issue = buf
        del issue_data


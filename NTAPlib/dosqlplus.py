#! /usr/bin/python
###########################################################################
# (c) 2019 NetApp Inc. (NetApp), All Rights Reserved
#
# NetApp disclaims all warranties, excepting NetApp shall provide
# support of unmodified software pursuant to a valid, separate,
# purchased support agreement.  No distribution or modification of
# this software is permitted by NetApp, except under separate
# written agreement, which may be withheld at NetApp's sole
# discretion.
#
# THIS SOFTWARE IS PROVIDED BY NETAPP "AS IS" AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL NETAPP BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
# OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Created by Jeffrey Steiner, jfs@netapp.com
#
###########################################################################
import sys
import os
import userio
import subprocess
import pwd
import grp


def dosqlplus(sid, sqlcommands, **kwargs):
    import orautils
    passkwargs = {'bufsize': 1, 'stdin': subprocess.PIPE, 'stdout': subprocess.PIPE, 'stderr': subprocess.PIPE, 'shell': False}

    commandblock = 'set echo off;\nset feedback off;\nset heading off;\nset pagesize 0;\nset linesize 500;\n'
    if 'quiet' in kwargs.keys() and kwargs['quiet'] is False:
        commandblock = ''

    if 'home' in kwargs.keys():
        oraclehome = kwargs['home']
    else:
        oraclehome = orautils.getoraclehome(sid)
        if oraclehome is None:
            return({'RESULT': 1,
                    'STDOUT': [],
                    'ERRORFLAG': 1,
                    'STDERR': ['Unable to get ORACLE_HOME for ' + sid]})

    if 'base' in kwargs.keys():
        oraclebase = kwargs['base']
    else:
        oraclebase = orautils.getoraclebase(oraclehome)
        if oraclebase is None:
            return({'RESULT': 1,
                    'STDOUT': [],
                    'ERRORFLAG': 1,
                    'STDERR': ['Unable to get ORACLE_BASE for ' + sid]})

    if 'user' in kwargs.keys():
        useraccount = kwargs['user']
        try:
            checkuid = pwd.getpwnam(kwargs['user']).pw_uid
        except:
            return({'RESULT': 1,
                    'STDOUT': [],
                    'ERRORFLAG': 1,
                    'STDERR': ['Unknown user: ' + kwargs['user']]})
    else:
        useraccount = orautils.getoracleuser(oraclehome)
        if useraccount is None:
            return({'RESULT': 1,
                    'STDOUT': [],
                    'ERRORFLAG': 1,
                    'STDERR': ['Unable to get Oracle user for ' + oraclehome]})
        else:
            checkuid = pwd.getpwnam(useraccount).pw_uid

    if not checkuid == os.geteuid():
        if os.geteuid() == 0:
            passkwargs['preexec_fn'] = changeuser(useraccount, showchange=False)
        else:
            return({'RESULT': 1,
                    'STDOUT': [],
                    'ERRORFLAG': 1,
                    'STDERR': ['Only root can run sqlplus as alternate user']})

    if 'printstdout' in kwargs.keys():
        printstdout = kwargs['printstdout']
    else:
        printstdout = False

    if type(sqlcommands) is list:
        for line in sqlcommands:
            commandblock = commandblock + line + "\n"
    else:
        commandblock = commandblock + sqlcommands + "\n"

    if not (commandblock[-5: -1]).lower() == 'exit;':
        commandblock = commandblock + "exit;\n"

    stdout = []
    stderr = []
    returnhash = {}
    returnhash['ERRORFLAG'] = 0
    mypath = "/bin: /usr/bin:/usr/local/bin:" + oraclehome + "/bin"
    myldlibrarypath = oraclehome + "/lib"
    myenv = {"PATH":  mypath,
             "LD_LIBRARY_PATH": myldlibrarypath,
             "ORACLE_HOME": oraclehome,
             "ORACLE_SID": sid,
             "ORACLE_BASE": oraclebase}
    passkwargs['env'] = myenv
    sqlpluscmd = subprocess.Popen(['sqlplus', '-S', '/', 'as', 'sysdba'], **passkwargs)

    if printstdout:
        sqlpluscmd.stdin.write(commandblock)
        while sqlpluscmd.poll() is None:
            nextline = sqlpluscmd.stdout.readline()
            nextline = nextline.rstrip()
            if len(nextline) > 0:
                userio.message(nextline)
                stdout.append(nextline)
        remainder = sqlpluscmd.stdout.readlines()
        for nextline in remainder:
            if len(nextline) > 0:
                userio.message(nextline)
                stdout.append(nextline)
        stderr = sqlpluscmd.stderr.readlines()
    else:
        cmdout, cmderr = sqlpluscmd.communicate(commandblock)
        lines = cmdout.splitlines()
        for line in lines:
            if len(line) > 0:
                stdout.append(line)
        lines = cmderr.splitlines()
        for line in lines:
            if line(line) > 0:
                stderr.append(line)

    for line in stdout:
        if line[: 5] == 'ERROR' or line[:20] == 'ORACLE not available' or line[:9] == 'ORA-01034:':
            returnhash['ERRORFLAG'] = 1

    returnhash['STDOUT'] = stdout
    returnhash['STDERR'] = stderr
    returnhash['RESULT'] = sqlpluscmd.returncode
    return(returnhash)


def changeuser(user, **kwargs):
    if 'showchange' in kwargs.keys():
        showchange = kwargs['showchange']
    else:
        showchange = False
    userinfo = pwd.getpwnam(user)
    newuid = userinfo.pw_uid
    newgid = userinfo.pw_gid
    grouplist = [newgid]
    allgroups = grp.getgrall()
    for item in allgroups:
        if user in item[3]:
            grouplist.append(item[2])

    def set_ids():
        if showchange:
            userio.message("Changing GID to " + str(newgid))
        os.setgid(newgid)
        if showchange:
            userio.message("Changing group memberships to " + str(grouplist))
        os.setgroups(grouplist)
        if showchange:
            userio.message("Changing user to " + user)
        os.setuid(newuid)
    return set_ids

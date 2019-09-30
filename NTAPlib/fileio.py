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
import random

if os.name == 'posix':
    import pwd
    import grp


def forcemkdir(path, **kwargs):
    quiet = True

    if 'quiet' in kwargs.keys():
        quiet = kwargs['quiet']
    if not os.path.exists(path):
        if not quiet:
            userio.message("Creating directory: " + path)
        try:
            os.makedirs(path)
        except Exception as e:
            if not quiet:
                userio.message("Unable to create directory: ")
                userio.message(str(e))
                return(False)
    else:
        if not quiet:
            userio.message("Directory already exists: " + path)

    if 'user' in kwargs.keys():
        if kwargs['user'] is None:
            if not quiet:
                userio.message("User passed was 'None'")
                return(False)

        if not quiet:
            userio.message("Setting user ownership of " + path + " to " + kwargs['user'])
        try:
            newuid = pwd.getpwnam(kwargs['user']).pw_uid
        except Exception as e:
            if not quiet:
                userio.message("Unknown user: " + kwargs['user'])
                userio.message(str(e))
                return(False)
        try:
            os.chown(path, newuid, -1)
        except Exception as e:
            if not quiet:
                userio.message("Unable to set user of " + path + " to " + kwargs['user'])
                userio.message(str(e))
                return(False)

    if 'group' in kwargs.keys():
        if kwargs['group'] is None:
            if not quiet:
                userio.message("Group passed was 'None'")
                return(False)
        if not quiet:
            userio.message("Setting group ownership of " + path + " to " + kwargs['group'])
        try:
            newgid = grp.getgrnam(kwargs['group']).gr_gid
        except Exception as e:
            if not quiet:
                userio.message("Unknown group: " + kwargs['group'])
                userio.message(str(e))
                return(False)
        try:
            os.chown(path, -1, newgid)
        except Exception as e:
            if not quiet:
                userio.message("Unable to set group of " + path + " to " + kwargs['group'])
                userio.message(str(e))
                return(False)

    if 'mode' in kwargs.keys():
        try:
            octalmode = int(str(kwargs['mode']), 8)
        except Exception as e:
            if not quiet:
                userio.message("Invalid mode: " + str(kwargs['mode']))
                userio.message(str(e))
                return(False)
                return(False)
        if not quiet:
            userio.message("Setting mode of " + path + " to " + str(kwargs['mode']))
        try:
            os.chmod(path, octalmode)
        except Exception as e:
            if not quiet:
                userio.message("Unable to set mode of " + path + " to " + str(kwargs['mode']))
                userio.message(str(e))
                return(False)
    return(True)


def getpathinfo(path):
    resultdict = {}
    if os.path.isdir(path):
        resultdict['ISDIR'] = True
        resultdict['ISFILE'] = False
    elif os.path.isfile(path):
        resultdict['ISDIR'] = False
        resultdict['ISFILE'] = True
    else:
        resultdict['ISDIR'] = False
        resultdict['ISFILE'] = False
        return(resultdict)
    pathdata = os.stat(path)
    resultdict['UID'] = pathdata.st_uid
    resultdict['GID'] = pathdata.st_gid
    resultdict['USER'] = pwd.getpwuid(pathdata.st_uid).pw_name
    resultdict['GROUP'] = grp.getgrgid(pathdata.st_gid).gr_name
    resultdict['PERMS'] = oct(pathdata.st_mode & 0777)
    return(resultdict)


def checkfileprotection(filepath):
    servicename = 'checkfileprotection'
    returncode = 1
    try:
        tempfilehandle = open(filepath, 'r')
        userio.message(servicename, "Found file at " + filepath)
    except Exception as e:
        userio.message(servicename, "Failed to open " + filepath + " for reading")
        userio.message(str(e))
        return(0)
    if os.stat(filepath).st_uid == 0:
        userio.message(servicename, "File " + filepath + " is owned by root")
    else:
        userio.message(servicename, "File " + filepath + " not owned by root")
        return(0)
    mask = oct(os.stat(filepath).st_mode & 0777)
    if mask == '0600':
        userio.message(servicename, "File " + filepath + " has permissions 0600")
    else:
        userio.message(servicename, "File " + filepath + " is not secure")
        return(0)
    return(returncode)


def decryptpath(encryptedpath, keyfile):
    servicename = 'decrypt'
    fh = open(encryptedpath, 'rb+')
    encrypteddata = fh.read()[:-32]
    fh.seek(-32, 2)
    iv = fh.read(32)
    fh.close()
    mypath = "/bin:/usr/bin:/usr/local/bin:"
    myldlibrarypath = "/lib"
    myenv = {"PATH": mypath, "LD_LIBRARY_PATH": myldlibrarypath}
    procargs = ['openssl', 'enc', '-d', '-aes-256-cbc', '-z', '-kfile', keyfile, '-iv', iv]
    sslprocess = subprocess.Popen(procargs,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  stdin=subprocess.PIPE,
                                  shell=False,
                                  env=myenv)
    out, err = sslprocess.communicate(input=encrypteddata)
    if len(err) > 0:
        for line in out.split("\n"):
            userio.message(servicename, "  stdout: " + line)
        for line in err.split("\n"):
            userio.message(servicename, "  stderr: " + line)
        userio.messageanddie("Fatal openssl decryption error")
    return(out)


def encryptpath(plaintextstring, encryptedpath, keyfile):
    if not checkfile(encryptedpath, 'w') == 0:
        releaselock()
        messageanddie('Could not open file for writing' + encryptedpath)
    iv = ''.join(random.choice('0123456789abcdef') for _ in range(32))
    mypath = "/bin:/usr/bin:/usr/local/bin:"
    myldlibrarypath = "/lib"
    myenv = {"PATH": mypath, "LD_LIBRARY_PATH": myldlibrarypath}
    procargs = ['openssl', 'enc', '-aes-256-cbc', '-z', '-kfile', keyfile, '-iv', iv, '-out', encryptedpath]
    sslprocess = subprocess.Popen(procargs,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  stdin=subprocess.PIPE,
                                  shell=False,
                                  env=myenv)
    out, err = sslprocess.communicate(input=plaintextstring)
    if len(out) > 0 or len(err) > 0:
        message("Fatal openssl encryption error")
        for line in out.split("\n"):
            message("   stdout: " + line)
        for line in err.split("\n"):
            message("   stderr: " + line)
        sys.exit(1)
    fh = open(encryptedpath, 'ab')
    fh.write(iv)
    fh.close()
    return(0)


def setownership(path, **kwargs):
    newuid = -1
    newgid = -1
    for key in kwargs.keys():
        if key == 'user':
            try:
                newuid = pwd.getpwnam(kwargs[key]).pw_uid
            except:
                return(False)
        elif key == 'group':
            try:
                newgid = grp.getgrnam(kwargs[key]).gr_gid
            except:
                return(False)
        else:
            return(False)

    try:
        os.chown(path, newuid, newgid)
        return(True)
    except:
        return(False)

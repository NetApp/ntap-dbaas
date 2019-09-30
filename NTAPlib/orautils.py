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
import os
import pwd
from doprocess import doprocess

oratablocation = '/etc/oratab'


def getoraclehome(localsid):
    try:
        oratablines = open(oratablocation, 'r').read().splitlines()
    except:
        return(None)
    for line in oratablines:
        oratabfields = line.split(':')
        if oratabfields[0] == localsid:
            return(oratabfields[1])
    return(None)


def getoraclebase(oraclehome):
    oracleuser = getoracleuser(oraclehome)
    if oracleuser is None:
        return(None)

    out = doprocess(oraclehome + "/bin/orabase",
                    user=oracleuser,
                    env={'ORACLE_HOME': oraclehome, 'LIB': oraclehome + '/lib'})

    if out['RESULT'] == 0:
        if os.path.exists(out['STDOUT'][-1]):
            return(out['STDOUT'][-1])
        else:
            return(None)
    else:
        return(None)


def getoracleuser(oraclehome):
    try:
        oracleuid = os.stat(oraclehome).st_uid
        oracleuser = pwd.getpwuid(oracleuid).pw_name
        return(oracleuser)
    except:
        return(None)

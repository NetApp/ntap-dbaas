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
import getopt
import os
import getpass

single = '1'
multi = 'any'


def validateoptions(sysargs, validoptions, **kwargs):
    returndict = {}
    returndict['MODE'] = None
    returndict['OPTS'] = {}
    usage = "Error: Unable to process arguments"
    for key in kwargs.keys():
        if key == 'usage':
            usage = kwargs[key]
        if key == 'knownmodes':
            if len(sysargs) > 0 and sys.argv[1] not in knownmodes:
                fail(usage)
            else:
                returndict['mode'] = sysargs[1]

    if len(sysargs) == 0:
        fail(usage)

    if type(validoptions) is dict:
        optionlist = validoptions.keys()
    else:
        optionlist = validoptions

    try:
        options, args = getopt.getopt(sysargs, '', optionlist)
    except getopt.GetoptError as e:
        fail(str(e))
    except Exception as e:
        error(str(e))
        fail(usage)

    print validoptions

    for o, a in options:
        barearg = o
        if o.startswith('--'):
            barearg = o[2:]
        if type(validoptions) is dict:
            bareoption = set([barearg, barearg + "="]).intersection(validoptions.keys()).pop()
            if validoptions[bareoption] == 'str':
                truevalue = str(a)
            elif validoptions[bareoption] == 'int':
                truevalue = int(a)
            elif validoptions[bareoption] == 'bool':
                truevalue = True
            elif validoptions[bareoption] == 'duration':
                truevalue = duration2seconds(a)
                if not truevalue:
                    fail("Illegal value for --" + barearg)
        returndict['OPTS'][barearg] = truevalue

    if 'required' in kwargs.keys():
        for item in kwargs['required']:
            if type(item) is str:
                if item not in returndict['OPTS'].keys():
                    fail("--" + item + " is required")
            elif type(item) is list:
                if not set(item).intersection(set(returndict['OPTS'].keys())):
                    fail("One of the following arguments is required: --" + ' --'.join(item))

    if 'dependent' in kwargs.keys():
        for key in kwargs['dependent'].keys():
            if key in returndict['OPTS'].keys():
                for item in kwargs['dependent'][key]:
                    if type(item) is str:
                        if item not in returndict['OPTS'].keys():
                            fail("Argument --" + key + " requires the use of ---" + item)
                    elif type(item) is list:
                        if not set(item).intersection(set(returndict['OPTS'].keys())):
                            fail("Argument --" + key + " requires one of the following arguments: --" + ' --'.join(item))

    return(returndict)


def basicmenu(**kwargs):
    returnnames = False
    localchoices = list(kwargs['choices'])
    if 'control' in kwargs.keys():
        localcontrol = kwargs['control']
    else:
        localcontrol = single
    if 'header' in kwargs.keys():
        localheader = kwargs['header']
    if localcontrol == multi:
        localheader = "Select one or more of the following"
    else:
        localheader = "Select one of the following"
    if 'prompt' in kwargs.keys():
        localprompt = kwargs['prompt']
    else:
        localprompt = 'Selection'
    if 'sort' in kwargs.keys():
        if kwargs['sort']:
            localchoices.sort()
    if 'returnnames' in kwargs.keys():
        if kwargs['returnnames']:
            returnnames = kwargs['returnnames']
    if 'nowait' in kwargs.keys():
        nowait = kwargs['nowait']
    else:
        nowait = False
        localchoices.append('Continue')

    proceed = False
    selected = []
    while not proceed:
        message(localheader)
        for x in range(0, len(localchoices)):
            if nowait:
                field = "(" + str(x+1) + ") "
                message(field + localchoices[x])
            else:
                field = str(x+1) + ". "
                if x+1 in selected:
                    message("[X] " + field + localchoices[x])
                else:
                    message("[ ] " + field + localchoices[x])
        number = selectnumber(len(localchoices), prompt=localprompt)
        if nowait:
            if number <= len(localchoices):
                selected = [number]
                proceed = True
        else:
            if number == len(localchoices):
                if len(selected) < 1:
                    linefeed()
                    message("Error: Nothing selected")
                    linefeed()
                else:
                    proceed = True
            elif number in selected:
                if localcontrol == multi:
                    selected.remove(number)
            else:
                if localcontrol == multi:
                    selected.append(number)
                elif localcontrol == single:
                    selected = [number]
    if returnnames:
        newlist = []
        for item in selected:
            newlist.append(localchoices[item-1])
        return(newlist)
    return(selected)


def ctrlc(signal, frame):
    sys.stdout.write("\nSIGINT received, exiting...\n")
    sys.exit(1)


def banner(message):
    width = 80
    fullstring = ''
    borderstring = ''
    for x in range(0, width):
        fullstring = fullstring+'#'
    for x in range(0, width-6):
        borderstring = borderstring + " "
    sys.stdout.write(fullstring + "\n")
    sys.stdout.write("###" + borderstring + "###\n")
    if type(message) is str:
        padding = ''
        for x in range(0, width-8-len(message)):
            padding = padding + ' '
        messagestring = message + padding + "###"
        sys.stdout.write("###  " + messagestring + "\n")
    elif type(message) is list:
        for line in message:
            padding = ''
            for x in range(0, width-8-len(line)):
                padding = padding + ' '
            messagestring = line + padding + "###"
            sys.stdout.write("###  " + messagestring + "\n")
    sys.stdout.write("###" + borderstring + "###\n")
    sys.stdout.write(fullstring + "\n")
    sys.stdout.flush()


def message(args, **kwargs):
    if 'prenewline' in kwargs.keys():
        if kwargs['prenewline']:
            linefeed()
    leader = ''
    if 'service' in kwargs.keys():
        leader = leader + kwargs['service'] + ": "
    if type(args) is list:
        for line in args:
            sys.stdout.write(leader + line + "\n")
            sys.stdout.flush()
    else:
        sys.stdout.write(leader + str(args) + "\n")
        sys.stdout.flush()


def error(args, **kwargs):
    if type(args) is list:
        for line in args:
            sys.stdout.write("ERROR: " + line + "\n")
    else:
        sys.stdout.write("ERROR: " + args + "\n")


def fail(args, **kwargs):
    if type(args) is list:
        for line in args:
            sys.stdout.write("ERROR: " + line + "\n")
    else:
        sys.stdout.write("ERROR: " + args + "\n")
    sys.exit(1)


def warn(args, **kwargs):
    if 'prenewline' in kwargs.keys():
        if kwargs['prenewline']:
            linefeed()
        else:
            linefeed()
    if type(args) is list:
        for line in args:
            sys.stdout.write("WARNING: " + line + "\n")
            sys.stdout.flush()
    else:
        sys.stdout.write("WARNING: " + args + "\n")
        sys.stdout.flush()


def justexit():
    sys.stdout.write("Exiting... \n")
    sys.exit(0)


def linefeed():
    sys.stdout.write("\n")
    sys.stdout.flush()


def yesno(string):
    answer = None
    while answer is None:
        usersays = raw_input(string + " (y/n) ").lower()
        if usersays == 'y':
            answer = True
        elif usersays == 'n':
            answer = False
    return(answer)


def ask(string, **kwargs):
    answer = None
    if 'default' in kwargs.keys():
        defaultstring = ' [' + kwargs['default'] + ']'
    else:
        defaultstring = ''
    if 'hide' in kwargs.keys() and kwargs['hide']:
        usersays = getpass.getpass(string + defaultstring + ": ")
    else:
        usersays = raw_input(string + defaultstring + ": ")
    if usersays == '' and not defaultstring == '':
        return(kwargs['default'])
    else:
        return(usersays)


def selectnumber(*args, **kwargs):
    answer = 0
    maximum = args[0]
    if 'prompt' in kwargs.keys():
        prompt = kwargs['prompt']
    else:
        prompt = "Selection"
    while answer < 1 or answer > maximum:
        try:
            answer = int(raw_input(prompt + ": (1-" + str(maximum) + "): "))
        except KeyboardInterrupt:
            justexit()
        except Exception as e:
            answer = 0
    return(answer)


def providenumber(maximum):
    answer = 0
    while answer < 1 or answer > maximum:
        try:
            answer = int(raw_input("(1-" + str(maximum) + "): "))
        except KeyboardInterrupt:
            justexit()
        except Exception as e:
            answer = 0
    return(answer)


def grid(listoflists, **kwargs):
    totalcolumns = len(listoflists[0])
    totalrows = len(listoflists)
    columnwidths = {}
    for x in range(0, totalcolumns):
        columnwidths[x] = len(listoflists[0][x])
    for y in range(0, totalrows):
        for x in range(0, totalcolumns):
            if listoflists[y][x] is not None and len(listoflists[y][x]) > columnwidths[x]:
                columnwidths[x] = len(listoflists[y][x])
    firstline = ''
    secondline = ''
    if 'noheader' in kwargs.keys() and kwargs['noheader']:
        for x in range(0, totalcolumns):
            firstline = firstline + listoflists[0][x] + " " * (columnwidths[x] - len(listoflists[0][x]) + 1)
        message(firstline.rstrip())
    else:
        for x in range(0, totalcolumns):
            firstline = firstline + listoflists[0][x].upper() + " " * (columnwidths[x] - len(listoflists[0][x]) + 1)
            secondline = secondline + '-' * columnwidths[x] + " "
        message(firstline.rstrip())
        message(secondline.rstrip())
    for y in range(1, totalrows):
        nextline = ''
        for x in range(0, totalcolumns):
            if listoflists[y][x] is not None:
                nextline = nextline + listoflists[y][x]
            if listoflists[y][x] is None:
                nextline = nextline + " " * (columnwidths[x] + 1)
            else:
                nextline = nextline + " " * (columnwidths[x] - len(listoflists[y][x]) + 1)
        message(nextline.rstrip())


def duration2seconds(value):
    if not value[-1].isalpha:
        value = value + 'd'
    if value[-1] == 's':
        return(int(a[:-1]))
    elif value[-1] == 'm':
        return(int(a[:-1])*60)
    elif value[-1] == 'h':
        return(int(a[:-1])*60*60)
    elif value[-1] == 'd':
        return(int(value[:-1])*60*60*24)
    else:
        return(None)

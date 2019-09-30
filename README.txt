This is a set of dockerfiles and associated utilities that manage Oracle databases within containers.

This is an initial release, and undoubtedly has some gaps, but I'm eager for feedback and ready to fix problems and refine the code. Contact me directly at jfs@netapp.com for assistance.

And now, the disclamers:

(c) 2019 NetApp Inc. (NetApp), All Rights Reserved

NetApp disclaims all warranties, excepting NetApp shall provide
support of unmodified software pursuant to a valid, separate,
purchased support agreement.  No distribution or modification of
this software is permitted by NetApp, except under separate
written agreement, which may be withheld at NetApp's sole
discretion.

THIS SOFTWARE IS PROVIDED BY NETAPP "AS IS" AND ANY EXPRESS OR
IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL NETAPP BE LIABLE FOR ANY DIRECT,
INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
OF THE POSSIBILITY OF SUCH DAMAGE.

A more detailed explanation of how I created this code is available at
 
 https://words.ofsteiner.com/

There might be more posts by the time you read this README, but look down the page. There's a 5-part series on this topic.

The imporant things are as follows:

DATABASE LAYOUT

The database layout is hard-coded to use the following format:

 /oradata/[SID]
 /logs/[SID]/dbconfig   (used for basic files like oratab and spfiles)
 /logs/[SID]/arch       (archive logs)
 /logs/[SID]/ctrl       (control files)
 /logs/[SID]/redo       (redo logs)

The reason for this is predictability. The various utilities and approach to snapshots requires
placing data in known locations with known snapshot schedules. 

SNAPSHOT SCHEDULES

At the start of the main dbaas management utility, you'll see a couple of variables for snapshot policies. They are currently set as "docker-datafiles" and "docker-logs". You can customize these as required, but it's important that the policy creates datafile snapshots *before* it creates log snapshots. 

VOLUME SIZES

You'll also see the default datafile and log volume sizes set at the start of dbfvolsize and logvolsize

SSH ACCESS

Replace the contents of NTAP.authorized_keys with the authorized_keys file you'd like to place in the container. 

DEBUGGING dbaas OPERATIONS

You can always use --trace to follow the logs of a provision, create, or clone command. 

You can also use --nogo to print the kubectl commands that would have been executed. You can then read the text and see what might have gone wrong.

Finally, sometimes commands fail. The --spin argument will cause the database startup process to wait on an infinite "ping localhost" operation rather than trying to tail the Oracle alert logs. This sometimes helps you troubleshoot container startup problems.

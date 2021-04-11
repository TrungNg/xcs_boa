#!/bin/sh
#
# Force Bourne Shell if not Sun Grid Engine default shell (you never know!)
#
#$ -S /bin/sh
#
# I know I have a directory here so I'll use it as my initial working directory
#
#$ -wd /vol/grid-solar/sgeusers/baotrung/xcs_boa
#
# End of the setup directives
#
# Now let's do something useful, but first change into the job-specific
# directory that should have been created for us
#
# Check we have somewhere to work now and if we don't, exit nicely.
#
if [ -d /local/tmp/baotrung/$JOB_ID ]; then
        cd /local/tmp/baotrung/$JOB_ID
        cp -R /vol/grid-solar/sgeusers/baotrung/xcs_boa/source/. /local/tmp/baotrung/$JOB_ID
else
        echo "Uh oh ! There's no job directory to change into "
        echo "Something is broken. I should inform the programmers"
        echo "Save some information that may be of use to them"
        echo "There's no job directory to change into "
        echo "Here's LOCAL TMP "
        ls -la /local/tmp
        echo "AND LOCAL TMP BAOTRUNG "
        ls -la /local/tmp/baotrung
        echo "Exiting"
        exit 1
fi
#
# Now we are in the job-specific directory so now can do something useful
#
echo ==UNAME==
uname -n
echo ==WHO AM I and GROUPS==
id
groups
echo ==SGE_O_WORKDIR==
echo $SGE_O_WORKDIR
#
# OK, where are we starting from and what's the environment we're in
#
echo ==RUN HOME==
pwd
ls
echo ==ENV==
env
echo ==SET==
set
#
echo == WHATS IN LOCAL TMP BAOTRUNG JOB_ID AT THE START==
ls -la
#
# Now Run your program
#
python3.6 xcs_run.py
#
echo ==AND NOW, HAVING DONE SOMTHING USEFUL AND CREATED SOME OUTPUT==
ls -la
ls -la Local_Output/
#
# Now we move the output to a place to pick it up from later
#  noting that we need to distinguish between the TASKS
#  (really should check that directory exists too, but this is just a test)
#
cp -r /local/tmp/baotrung/$JOB_ID/Local_Output/  /vol/grid-solar/sgeusers/baotrung/xcs_boa/source/$JOB_ID/
#
echo "Ran through OK"

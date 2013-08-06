#!/bin/bash
source /etc/profile

# Run script as...
# check_du.sh -s SERVERNAME -e EMAILADDR -d DEVICE -m MODE -p PERC
# MODE:
# report := email report regardless
# warn := email report if warning met
#
# PERC:
# Disk space threshold as a percentage out of 100 (ie: 90 = 90%)
#
# EXAMPLE:
# check_du.sh -s Equinox -e hi@mikemead.me -d /dev/sda1 -m warn -p 90

while getopts s:e:d:m:p: option
do
        case "${option}"
        in
                s) SERVERNAME=${OPTARG};;
                e) EMAILADDR=${OPTARG};;
                d) DEVICE=${OPTARG};;
                m) MODE=${OPTARG};;
                p) PERC=${OPTARG};;
        esac
done

if [ -z "$PERC" ]
then
        let PERC=90
fi

let p=`df -k $DEVICE | grep -v ^File | awk '{printf ("%i",$3*100 / $2); }'`

if [ "$MODE" = "report" ]
then
        df -h $DEVICE | mail -s "$SERVERNAME - $DEVICE Monthly Report" $EMAILADDR
elif [ "$MODE" = "warn" ]
then
        if [ $p -ge $PERC ]
        then
                df -h $DEVICE | mail -s "$SERVERNAME - $DEVICE is low on space!" $EMAILADDR
        fi
fi

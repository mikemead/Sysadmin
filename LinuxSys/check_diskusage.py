#!/usr/bin/env python
from __future__ import division
from subprocess import PIPE, Popen
import psutil
import smtplib
from email.mime.text import MIMEText

def main():
        # Send email alerts to
        emailto = [
                'email@example.com'
        ]
        emailfrom = 'ServerName@example.com'
        server = 'ServerName'
		smtpserver = 'smtpserver.example.com'

        # Disks to check
        disks = {
                "root": { "disk": "/" },
                "home": { "disk": "/home" }
        }

        error_count = 0

        # Loops through all disks and find those with less than 10% disk space free
        for key, value in disks.iteritems():
                disk = psutil.disk_usage(value['disk'])
                disk_percent_used = disk.percent
                disk_percent_free = 100 - disk_percent_used
                if disk_percent_free <= 10:
                        value['error'] = 1
                        value['free'] = disk_percent_free
                        value['used'] = disk_percent_used
                        error_count = error_count + 1
                else:
                        value['error'] = 0
                disks[key] = value

        # Report any errors
        if error_count > 0:
                msg_body = ''
                for key, value in disks.iteritems():
                        print value['error']
                        if value['error'] > 0:
                                msg_body = 'Partition ' + value['disk'] + ' is using ' + str(value['used']) + '% of the available disk space'
                msg = MIMEText(msg_body)
                msg['Subject'] = server + ' Low Disk Space'
                msg['From'] = emailfrom
                msg['To'] = ','.join(emailto)
                s = smtplib.SMTP(smtpserver)
                s.sendmail(emailfrom, emailto, msg.as_string())
                s.quit

if __name__ == '__main__':
        main()
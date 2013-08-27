#!/usr/bin/env python2.6
import subprocess
import re
import smtplib
from email.mime.text import MIMEText

def alarm_found(level, status_txt):
        # Send email alerts to
        emailto = [
                'hi@mikemead.me'
        ]
        emailfrom = 'pbx@pbx.local'
        server = 'PBX'
		smtpserver = 'smtp.pbx.local'

        # Let's get the status of all channels
        proc_channels = subprocess.Popen(['/usr/sbin/asterisk -rx "dahdi show channels"'], stdout=subprocess.PIPE, shell=True)
        channels_stdout = proc_channels.stdout.read()

        # Prepare and send alert email(s)
        msg = MIMEText(status_txt + '\n' + channels_stdout)
        msg['Subject'] = server + ' ' + level + ' Alarm(s) Found'
        msg['From'] = emailfrom
        msg['To'] = ','.join(emailto)
        s = smtplib.SMTP(smtpserver)
        s.sendmail(emailfrom, emailto, msg.as_string())
        s.quit

def main():
        # Let's get the status of DAHDI
        proc_status = subprocess.Popen(['/usr/sbin/asterisk -rx "dahdi show status"'], stdout=subprocess.PIPE, shell=True)
        status_stdout = proc_status.stdout.read()

        if re.search(r'RED', status_stdout):
                # If RED alarm found :'(
                alarm_found('RED', status_stdout)
        elif re.search(r'YEL', status_stdout):
                # If YELLOW alarm found :(
                alarm_found('YELLOW', status_stdout)
        else:
                # No alarm found :)

if __name__ == '__main__':
        main()

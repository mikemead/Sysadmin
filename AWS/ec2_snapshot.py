from boto.ec2.connection import EC2Connection
from datetime import datetime
import sys
import boto.ec2
import sendgrid

#
# Usage: python ec2_snapshot.py volume_id server_name
#

# Specify Email address to send alerts to
email_addr = ""

# Sendgrid Auth
sg_user = ""
sg_pass = ""
sg_tag = ""

# AWS Details
aws_region = ""
aws_access_key_id = ""
aws_secret_access_key = ""

if len(sys.argv) < 3:
        print "Usage: python ec2_snapshot.py volume_id server_name"
        sys.exit(1)

vol_id = sys.argv[1]
server = sys.argv[2]

s = sendgrid.Sendgrid(sg_user, sg_pass, secure=True)

description = server + " backup taken at " + datetime.today().isoformat(' ')
msg = server + " EBS Snapshot "

try:
        conn_eu = boto.ec2.connect_to_region(aws_region, aws_access_key_id, aws_secret_access_key)
except:
        message = sendgrid.Message(email_addr, "[Failed] " + msg, msg + vol_id + " failed: Could not connect to AWS Region", msg + vol_id + " failed: Could not connect to AWS Region")
        message.add_to(email_addr, "MSP Alerts")
        s.web.send(message)
        sys.exit(1)

try:
        volumes = conn_eu.get_all_volumes([vol_id])
        volume = volumes[0]
except:
        message = sendgrid.Message(email_addr, "[Failed] " + msg, msg + vol_id + " failed: Invalid EBS Volume", msg + vol_id + " failed: Invalid EBS Volume")
        message.add_to(email_addr, sg_tag)
        s.web.send(message)
        sys.exit(1)

if volume.create_snapshot(description):
        message = sendgrid.Message(email_addr, "[Success] " + msg, msg + vol_id + " succeeded", msg + vol_id + " succeeded")
        snapshot_cleanup = True
else:
        message = sendgrid.Message(email_addr, "[Failed] " + msg, msg + vol_id + " failed", msg + vol_id + " failed!")
        snapshot_cleanup = False

message.add_to(email_addr, sg_tag)

s.web.send(message)

if snapshot_cleanup is True:
        snapshots = volume.snapshots()
        snapshot = snapshots[0]
		
        def date_compare(snap1, snap2):
                if snap1.start_time < snap2.start_time:
                        return -1
                elif snap1.start_time == snap2.start_time:
                        return 0
                return 1

        snapshots.sort(date_compare)
        delta = len(snapshots) - 3
        for i in range(delta):
                snapshots[i].delete()
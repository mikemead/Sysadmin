#!/usr/bin/env python
"""
Removes all members (or specified) member from specified queue and logs to agent_logout.log

Usage:
	python agent_logout.py -q QUEUE [-m MEMBER] [-a]
e.g.
        python agent_logout.py -q 4000 -m 1234 (Remove member 1234 from queue 4000)
        python agent_logout.py -q 4000 -a (Remove all members from queue 4000)
"""

import subprocess
import datetime
import sys
import getopt

def log_queue_member_removal(queue, member, name):
	"""
	Outputs to agent_logout.log the time and date and details of each member logged out of the specified queue.
	"""
	f = open("agent_logout.log", "a")
	f.write(str(datetime.datetime.today()) + ": " + name + "(" + member + ") logged out of queue " + str(queue) + "\n")
	f.close()

def remove_queue_member(queue, member):
	"""
	Removes specified member from specified Asterisk queue
	"""
	subprocess.Popen(['/usr/sbin/asterisk -rx "queue remove member ' + str(member) + ' from ' + str(queue) + '"'], stdout=subprocess.PIPE, shell=True)

def get_queue_members(queue):
	"""
	Returns details of specified queue 'asterisk -rx "queue show"'
	"""
	return subprocess.Popen(['/usr/sbin/asterisk -rx "queue show ' + str(queue) + '"'], stdout=subprocess.PIPE, shell=True)

def usage():
	print __doc__

def main(argv):
	queue, member, all = 0, 0, 0

	# Get specified options
	try:
		opts, args = getopt.getopt(argv, "q:m:ah")
	except getopt.GetoptError:
		usage()
		sys.exit(2)

	# Figure out what options we have and assign variables
	for opt, arg in opts:
		if opt in ("-h"):
			usage()
			sys.exit()
		elif opt in ("-q"):
			queue = arg
		elif opt in ("-m"):
			member = arg
		elif opt in ("-a"):
			all = 1

	# If a queue was specified and all members are to be removed
	if queue and all:
		queue_details = get_queue_members(queue)
		for line in queue_details.stdout:
			if "ext-local" in line:
				member = line.split(' from hint:')[0].split('(')
				remove_queue_member(queue, member[1])
				log_queue_member_removal(queue, member[1], member[0].strip())
	# If a queue was specified and a single member is to be removed
	elif queue and member:
		member_string = "Local/" + member + "@from-queue/n"
		remove_queue_member(queue, member_string)
		log_queue_member_removal(queue, member_string, "")
	else:
		usage()
		sys.exit()

if __name__ == '__main__':
	main(sys.argv[1:])

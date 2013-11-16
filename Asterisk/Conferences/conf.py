#!/usr/bin/env python
from subprocess import call
import imaplib
import smtplib
import email.utils
import re
import dbase
import uuid
import datetime
import string
import random
import os

def get_new_emails():
	""" Fetch new emails from specified IMAP server and account. Returns a list of all new emails. """
	try:
		# Connect to IMAP account
		imap_con = imaplib.IMAP4_SSL(config['imap_server'])
		imap_con.login(config['imap_username'], config['imap_password'])
		imap_con.select()

		try:
			# Retrieve all unread emails
			rcode, data = imap_con.search(None, '(UNSEEN)')

			if rcode == 'OK':
				try:
					# Process emails
					emails = []
					for num in data[0].split():
						rcode, data = imap_con.fetch(num, '(RFC822)')
						if rcode == 'OK':
							emails.append(data)
					return emails
				except:
					print "Error - Processing emails"
			else:
				print "Error - Fetching emails"
		except:
			print "Error - Unable to retrieve emails"
	except:
		print "Error - Connecting to IMAP mailbox"
	finally:
		# ALWAYS do this regardless of what happens above
		imap_con.close()
		imap_con.logout()

def process_emails(emails):
	""" Loops through a list of email (most likely from get_new_emails()) and returns a list of senders. """
	if emails:
		requests = []
		# For every email returned
		for data in emails:
			sender = {}
			# Let's find the sender's details in the email
			for email_part in data:
				if isinstance(email_part, tuple):
					msg = email.message_from_string(email_part[1])
					sender_string = msg['from']
					sender_parts = email.utils.parseaddr(sender_string)
					sname, semail = '', ''
					# Find an email address
					for s in sender_parts:
						if re.match(r"[^@]+@[^@]+\.[^@]+", s):
							semail = s
						else:
							sname = s

					if len(semail) > 3: # An email address was found!
						sender['email'] = semail

						if sname == '':
							sname = semail.split('@', 1)[0]
						sender['name'] = sname
						sender['created'] = 0
						sender['conf'] = ''
						requests.append(sender)
		return requests
	else:
		print "Error - Processing emails"
		return None

def pin_generator():
	""" Generates a pin code for conferences based on pin_length set in the configuration file """
	return ''.join(random.choice(string.digits) for x in range(config['pin_length']))

def create_conferences(requests):
	""" Creates and updates conferences for each request """
	db = dbase.connect(config['hostname'], config['username'], config['password'], config['database'])
	# For every request
	for index, request in enumerate(requests):
		# First - Find a free conference room
		db.execute("SELECT conf_id, exten FROM conference_rooms WHERE available=1 ORDER BY exten LIMIT 1")
		free_conf = db.fetchone()
		# Do we have a free/valid conference?
		if free_conf:
			try:
				conference_id = free_conf[0]
				conference_exten = free_conf[1]
				conference_pin = pin_generator()
				# Reserve the room
				db.execute("UPDATE conference_rooms SET available=0, expires_on=(NOW() + INTERVAL %s DAY), book_name=%s, book_email=%s, pin=%s WHERE conf_id=%s LIMIT 1", (str(config['conf_expire']), str(request['name']), str(request['email']), str(conference_id), str(conference_pin)))

				# Does the conference room exist in FreePBX?
				db.execute("SELECT exten FROM meetme WHERE exten=%s AND exten BETWEEN CAST(%s as UNSIGNED) AND CAST(%s as UNSIGNED) LIMIT 1", (str(conference_exten), str(config['start_exten']), str(config['end_exten'])))
				conf_exists = db.fetchone()

				if conf_exists: # Conf exists - Update it
					db.execute("UPDATE meetme SET userpin=%s, users=0 WHERE exten=%s AND description=CONCAT('Room ', %s) LIMIT 1",(str(conference_pin), str(conference_exten), str(conference_id)))
				else: # Conf does not exist - Create it
					db.execute("INSERT INTO meetme (exten, options, userpin, adminpin, description, joinmsg_id, music, users) VALUES (%s, %s, %s, '', %s, 0, 'default', 0)", (str(conference_exten), str(config['conf_options']), str(conference_pin), 'Room ' + str(conference_id)))

				requests[index]['created'] = 1
				requests[index]['conf'] = conference_exten
				requests[index]['pin'] = conference_pin
				requests[index]['expires'] = (datetime.datetime.now() + datetime.timedelta(days=int(config['conf_expire']))).strftime("%a %e %b %T")

			except:
				print "Error - Could not reserve conference room"
		else:
			print "Error - No free/valid conference room"
	return requests

def send_details(requests):
	""" Sends details of the conference room to the requester """
	sender = config['smtp_sender']
	s = smtplib.SMTP(config['smtp_server'])
	
	for request in requests:
		if request['created'] == 1:
			msg = "From:" + sender + "\nTo:" + request['email'] + "\nSubject: " + config['smtp_subject'] + " \n\nConference Number: " + request['conf'] + "\nConference Pin: " + request['pin'] + "\nExpires: " + request['expires'] + "\n\n" + config['smtp_message']
        	        s.sendmail(config['smtp_sender'], request['email'], msg)
	s.quit()

def apply_config():
	""" Builds FreePBX/Asterisk config from DB and reloads config """
	try:
		# Rebuild confs
		call('/var/lib/asterisk/bin/retrieve_conf', shell=True)
		# Reload confs
		call('/usr/local/sbin/amportal a r', shell=True)
		return True
	except:
		return None

def cleanup_conferences():
	""" Cleans up any expired conferences and sets a random pin """
	db = dbase.connect(config['hostname'], config['username'], config['password'], config['database'])

	# Find conference rooms that have expired
	db.execute("SELECT conf_id, exten FROM conference_rooms WHERE available=0 AND expires_on < CURDATE()")

	expired_confs = db.fetchall()
	if expired_confs:
		for conference in expired_confs:
			conference_id = conference[0]
			conference_exten = conference[1]
			conference_pin = pin_generator()

			# Change the pin on all expired conferences
			db.execute("UPDATE meetme SET userpin=%s, users=0 WHERE exten=%s AND description=CONCAT('Room ', %s) LIMIT 1",(str(conference_pin), str(conference_exten), str(conference_id)))

			# Switch the conference room flag to available
			db.execute("UPDATE conference_rooms SET available=1, book_name='', book_email='', pin=%s WHERE conf_id=%s LIMIT 1", (str(conference_id), str(conference_pin)))

def main():
	# Get all new unread emails
	emails = get_new_emails()

	# We found some unread emails! :)
	if emails:
		requests = process_emails(emails)

		# We found some requests!! :D
		if requests:
			requests = create_conferences(requests)
			if apply_config():
				send_details(requests)

	# Now the requests are processed, let's do some cleaning up
	cleanup_conferences()

if __name__ == "__main__":
	config = {}
	dir = os.path.dirname(__file__)
	config_file = os.path.join(dir, 'conferences.conf')
	execfile(config_file, config)
	main()
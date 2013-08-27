import-module ActiveDirectory

# Attachment threshold (users sending emails over the following limit will be emailed)
$attachment_threshold = 10 # Megabytes

# Hub Transport Server
$hubt = ""

# Email Template (HTML template)
$email_template = ""
$email_subject = ""
$email_from = "notifications@example.com"

# Import list of users already notified (we don't want to harrass them for each email they send!)
$xml_file = "already_notified.xml"
[xml]$already_notified = Get-Content $xml_file

# Output log file for errors
$logfile = "$(Get-Date -f yyyy-MM-dd).log"

# Function - Output to logfile
function Write-Logfile ([string]$logtext) {
	$ts = Get-Date -format g
	Add-Content $logfile "$($ts): $($logtext)"
}

$startdate = Get-Date (Get-Date).AddDays(-7) -Format d
$enddate = Get-Date -Format d

# Let's grab emails that meet the criteria for the past week
$emails = Get-MessageTrackingLog -Server $hubt -EventId "Send" -Start "$($startdate)" -End "$($enddate)" -ResultSize Unlimited | Select-Object * | Where {$_.TotalBytes -gt "$($attachment_threshold * 1024 * 1024)" }

# Let's find out what domains our Exchange infrastructure accepts
$accepted_domains = Get-AcceptedDomain | select DomainName

$emails_found = $emails.count
$users_to_notify = @()
$users_notified_count = 0

foreach ($email in $emails) {
	$found = $false
	
	# Does the senders domain match our own?
	if ($accepted_domains -match $email.Sender.Substring($email.Sender.IndexOf("@") + 1)) {
		# Yes - We don't need to do anything
	} else {
		# No - We don't want to send them an email
		$found = $true
		$emails_found -= 1
	}
	# Has the sender offended - I mean - sent a large attachment before
	foreach ($user in $already_notified.Users.User) {
		if ($email.Sender -eq $user.Email) {
			$found = $true
		}
	}
	# Was user found?
	if ($found) {
		# Yes - We don't need to do anything
	} else {
		# No - Let's add them to the XML file, and get ready to email them
		$users_to_notify += $email.Sender
		$users_notified_count += 1
		Write-Logfile "Notifying $($email.Sender): $([System.Math]::Round($email.TotalBytes /1024 /1024, 2))MB sent on $($email.Timestamp)"
		$new_user = (@($already_notified.Users.User)[0]).Clone()
		$new_user.Email = $email.Sender
		$new_user.DateNotified = [string] "$(Get-Date)"
		$already_notified.Users.AppendChild($new_user)
		$already_notified.Save($xml_file)
	}
}

# Send template email to users
$body = Get-Content $email_template | Out-String

foreach ($recip in $users_to_notify) {
	Send-MailMessage -To $recip -Subject $email_subject -Body $body -SmtpServer $hubt -From $email_from -BodyAsHtml
}

Write-Logfile "Notified $($users_notified_count) new users ($($emails_found - $users_notified_count) already notified)"
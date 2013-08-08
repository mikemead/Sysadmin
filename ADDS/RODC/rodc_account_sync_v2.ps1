import-module ActiveDirectory

# Input XML file for site list
[xml]$sitelist = Get-Content "C:\Scripts\RODC\sites.xml"

# Output log file for errors
$logfile = "C:\Scripts\RODC\logs\$(Get-Date -f yyyy-MM-dd).log"

# Function - Checks if AD OU exists, returns true/false
function Test-OUExist ([string]$ou) {
	try {
		if(!([adsi]::Exists("LDAP://$ou"))) {
		} else {
			$exists = $True
		}
	} catch { }
	return $exists
}

# Function - Checks if AD group exists, returns true/false
function Test-GroupExist ([string]$group) {
	$object = $null
	try {
		$object = Get-ADGroup -Identity "$group" -ErrorAction SilentlyContinue
	} catch { }
	
	if ($object -eq $null) {
		return $false
	} else {
		return $true
	}
}

# Function - Output to logfile
function Write-Logfile ([string]$logtext) {
	$ts = Get-Date -format g
	Add-Content $logfile "$($ts): $($logtext)"
}

# Function - Output a break to logfile
function Write-Logbreak {
	Add-Content $logfile $("-" * 55)
}

# Function - Synchronises OU to Group
function Sync-Accounts ($group, $ou, $type) {

	# Check if OU exists
	if ((Test-OUExist -ou $ou) -eq $true) {
			# Check if Group exists
			if ((Test-GroupExist -group $group) -eq $true) {
				# Get count of objects in group before sync
				$count_before = (Get-ADGroupMember $group).count
	
				# Sync objects from OU to group
				if ($type -eq 'user') {
					Get-ADUser -SearchBase $ou -Filter * | % { try { Add-ADGroupMember $group -Members $_ -ErrorAction SilentlyContinue -WhatIf } catch { } }
				} elseif ($type -eq 'computer') {
					Get-ADComputer -SearchBase $ou -Filter * | % { try { Add-ADGroupMember $group -Members $_ -ErrorAction SilentlyContinue -WhatIf } catch { } }
				} else {
					# No or invalid type
				}
				# Get count of objects in group after sync
				$count_after = (Get-ADGroupMember $group).count
				Write-Logfile "$($count_after - $count_before) $($type) accounts synchronised"
			} else {
				Write-Logfile "ERROR - Group [$($group)] does not exist"
			}
		} else {
			Write-Logfile "ERROR - OU [$($ou)] does not exist"
		}
}

# Foreach site in XML file...
foreach ($site in $sitelist.sites.site) {
	if ($site.enabled -eq 'true') {
		# Site enabled for sync
		Write-Logfile "Processing site - $($site.sitename)"

		# Sync computer accounts
		Sync-Accounts -group $site.ComputerGroup -ou $site.ComputerOU -type Computer
		
		# Sync user accounts
		Sync-Accounts -group $site.UserGroup -ou $site.UserOU -type User

	} else {
		# Site NOT enabled for sync
		Write-Logfile "Sync not enabled for site - $($site.sitename)"
	}
	Write-Logbreak
}
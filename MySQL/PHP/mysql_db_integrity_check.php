<?php

/**
** MySQL table integrity check script
**
** To run as a cron/scheduled task use:
** php mysql_db_integ_check.php -cron
**
** Run without the -cron switch for verbose output
**
** Script Created: 24/01/2013 by MM
**/

/**
**  Update these variables accordingly
**/

$this_server = 'MyServer'; 						// For alert purposes
$email_to = 'alerts@example.com'; 	// Email/Group to send alerts to
$email_from = 'myserver@example.com'; 	// Emails will come from

$params = array(
	'host' => 'localhost',
	'username' => 'mysqluser',
	'password' => 'mysqluserpass',
	'database' => 'database'
);

$alerts = array(
	'emailto' => $email_to,
	'emailfrom' => $email_from,
	'subject' => 'Alert: ' . $this_server . ' MySQL'
);

/**
** Start of code - you don't need to modify anything beyond here
**/

$errors = array();

$start_time = time();

if ($argv[1] == '-cron') { // If switch is cron
	$cron = true;
} else {
	$cron = false;
}

if (!$cron) { echo "Database: ".$params['database']."\n"; }

if (connectToDatabase($params)) {	// Connect to database
	// Get list of tables from DB
	if ($tables = getTables()) {
		while (list($table) = mysql_fetch_row($tables)) {	// Loop through all returned tables
			if (!$cron) { echo "Checking table $table\n"; }
			$status = checkTable($table);
			if ($status != 'OK') { // Not OK
				if (!$cron) { echo "Error! ". $status."\n"; }
				$errors[] = "Table '".$table."' might be corrupted (" . $status . ")";
			} else { // Run status check && OK
				if (!$cron) { echo "$table OK\n"; }
			}
		}
	} else {
		$errors[] = "Cannot return list of tables or database (" . $params['database'] . ") is empty";
	}
	
} else {
	$errors[] = "Cannot connect to MySQL server (".$params['host'].") or database (".$params['database'].")";
}

if (count($errors) > 0) { // If there's any errors
	$body = "MySQL table check of database '" . $params['database'] . "' has detected some errors on '" . $this_server . "'\r\n \r\n";
	foreach($errors as $error) {
		$body .= $error . "\r\n \r\n"; // + error + windows newline
	}
	mail($alerts['emailto'], $alerts['subject'], $body, 'From: '.$alerts['emailfrom']);
	if (!$cron) { echo "Email sent\n"; }
}

$total_time = time() - $start_time;

if (!$cron) { echo "Script took ".$total_time." seconds to complete\n"; }

function checkTable($table) {
	if ($table == 'blame' || $table == 'profile_values') {
		return 'OK';
	} else {
	$table_status = mysql_query("CHECK TABLE `".$table."` FAST");	// Check table
	
	if (!$table_status || mysql_num_rows($table_status) <= 0) { // Failed to get table status
		return false;
	} else { // Got table status
		mysql_data_seek($table_status, mysql_num_rows($table_status) - 1); // Seek to last status record returned
		$status = mysql_fetch_assoc($table_status); // Fetch status record we want
		if ($status['Msg_text'] == 'OK' || $status['Msg_text'] == 'Table is already up to date') { // Table status is OK :)
			return 'OK';
		} else { // Uh-oh - we might have a corrupted table :(
			return $status['Msg_type'] . ": " . $status['Msg_text'];
		}
	}	
	}
}

function getTables() {
	$tables = mysql_query("SHOW TABLES");
	if (!$tables || mysql_num_rows($tables) <=0) {	// Cannot return table list or DB empty
		return false;
	} else {	// Table list returned
		return $tables;
	}
}

function connectToDatabase($params) {
	if ($params['host'] != '' && $params['database'] != '') { // If parameters are set
		if (mysql_connect($params['host'], $params['username'], $params['password'])) { // If connection to mysql successful
			if (mysql_select_db($params['database'])) { // Connection to DB successful
				return true;
			} else {
				return false;
			}
		} else {
			return false;
		}
	} else {
		return false;
	}
}

?>
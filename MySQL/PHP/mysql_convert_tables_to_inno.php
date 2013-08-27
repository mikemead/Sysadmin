<?php

	/**
	*
	* PHP script to update all tables in selected database from MyISAM to InnoDB
	* It's very useful if you do not have shell access to the (web) server and it 
	* works cross platform as long as PHP is installed.
	*
	* Simply edit the variables below and run.
	*
	**/

	$db = "";
	$dsn = "mysql:host=localhost;dbname=$db";
	$username = "";
	$password = "";

	$from = 'MyISAM';
	$to = 'INNODB';

	try {
		$pdo = new PDO($dsn, $username, $password);
	}
	catch(PDOException $e) {
		die("Could not connect to the database\n");
	}

	$result = $pdo->query("
		SELECT TABLE_NAME
		FROM information_schema.TABLES
		WHERE TABLE_SCHEMA = '$db'
		AND ENGINE = '$from'
	");

	foreach($result as $row) {

		$success = $pdo->exec("ALTER TABLE {$row['TABLE_NAME']} ENGINE = $to");
		if($success) {
			echo "{$row['TABLE_NAME']} - success\n";
		} else {
			$info = $pdo->errorInfo();
			echo "{$row['TABLE_NAME']} - failed: $info[2]\n";
		}
	}
?>
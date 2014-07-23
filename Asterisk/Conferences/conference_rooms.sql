CREATE TABLE `conference_rooms` (
  `conf_id` int(11) NOT NULL AUTO_INCREMENT,
  `exten` varchar(50) NOT NULL,
  `pin` varchar(50) DEFAULT NULL,
  `last_updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `expires_on` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `book_name` varchar(100) DEFAULT NULL,
  `book_email` varchar(100) DEFAULT NULL,
  `available` tinyint(4) DEFAULT NULL,
  PRIMARY KEY (`conf_id`)
) ENGINE=MyISAM AUTO_INCREMENT=201 DEFAULT CHARSET=latin1;
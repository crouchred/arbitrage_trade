DROP TABLE IF EXISTS `balance`;
CREATE TABLE `balance` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `market` varchar(63) DEFAULT NULL,
  `coin` varchar(63) DEFAULT NULL,
  `amount` double DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `date` varchar(63) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `trade`;
CREATE TABLE `trade` (
  `orderid` bigint(20) NOT NULL,
  `market` varchar(63) DEFAULT NULL,
  `pair` varchar(63) DEFAULT NULL,
  `side` varchar(63) DEFAULT NULL,
  `plan` varchar(63) DEFAULT NULL,
  `timestamp` bigint(20) DEFAULT NULL,
  `price` double DEFAULT NULL,
  `amount` double DEFAULT NULL,
  `is_hedge` int(11) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `level` varchar(63) DEFAULT NULL,
  `deal_amount` double DEFAULT NULL,
  PRIMARY KEY (`orderid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

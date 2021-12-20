CREATE TABLE `Users` (
	`id` INT NOT NULL AUTO_INCREMENT,
	`name` VARCHAR(255) NOT NULL UNIQUE,
	`email` VARCHAR(255) NOT NULL UNIQUE,
	`hashed_password` VARCHAR(255) NOT NULL,
	PRIMARY KEY (`id`)
);


CREATE TABLE `Projects` (
	`id` INT NOT NULL AUTO_INCREMENT,
	`name` VARCHAR(255) NOT NULL,
	`description` VARCHAR(255),
	`owner_id` INT NOT NULL,
	FOREIGN KEY (`owner_id`)
		REFERENCES `Users` (`id`)
		ON DELETE CASCADE,
	PRIMARY KEY (`id`)
);


CREATE TABLE `Commits` (
	`id` INT NOT NULL AUTO_INCREMENT,
	`project_id` INT NOT NULL,
	`timestamp` TIMESTAMP NOT NULL DEFAULT NOW(),
	FOREIGN KEY (`project_id`)
		REFERENCES `Projects` (`id`)
		ON DELETE CASCADE,
	PRIMARY KEY (`id`)
);


CREATE TABLE `Files` (
	`id` INT NOT NULL AUTO_INCREMENT,
	`name` VARCHAR(255) NOT NULL,
	`file` BLOB NOT NULL,
	`project_id` INT NOT NULL,
	FOREIGN KEY (`project_id`)
		REFERENCES `Projects` (`id`)
		ON DELETE CASCADE,
	PRIMARY KEY (`id`)
);


CREATE TABLE `Changes` (
	`id` INT NOT NULL AUTO_INCREMENT,
	`type` VARCHAR(255) NOT NULL,
	`commit_id` INT NOT NULL,
	`file_id` INT NOT NULL,
	FOREIGN KEY (`commit_id`)
		REFERENCES `Commits` (`id`)
		ON DELETE CASCADE,
	FOREIGN KEY (`file_id`)
		REFERENCES `Files` (`id`)
		ON DELETE CASCADE,
	PRIMARY KEY (`id`)
);


CREATE TABLE `Participants` (
	`id` INT NOT NULL AUTO_INCREMENT,
	`project_id` INT NOT NULL,
	`user_id` INT NOT NULL,
	FOREIGN KEY (`project_id`)
		REFERENCES `Projects` (`id`)
		ON DELETE CASCADE,
	FOREIGN KEY (`user_id`)
		REFERENCES `Users` (`id`)
		ON DELETE CASCADE,
	PRIMARY KEY (`id`)
);


CREATE TABLE `Issues` (
	`id` INT NOT NULL AUTO_INCREMENT,
	`project_id` INT NOT NULL,
	`name` VARCHAR(255) NOT NULL,
	`description` VARCHAR(255) NOT NULL,
	FOREIGN KEY (`project_id`)
		REFERENCES `Projects` (`id`)
		ON DELETE CASCADE,
	PRIMARY KEY (`id`)
);

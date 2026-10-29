DROP DATABASE IF EXISTS election;
CREATE DATABASE election;
USE election;

CREATE TABLE positions (
    posID INT AUTO_INCREMENT PRIMARY KEY,
    posName VARCHAR(50) NOT NULL,
    numOfPositions INT NOT NULL,
    posStat VARCHAR(10) NOT NULL DEFAULT 'Active'
);

CREATE TABLE candidates (
    candID INT AUTO_INCREMENT PRIMARY KEY,
    candFName VARCHAR(50) NOT NULL,
    candMName VARCHAR(50),
    candLName VARCHAR(50) NOT NULL,
    posID INT NOT NULL,
    candStat VARCHAR(10) NOT NULL DEFAULT 'Active'
);

CREATE TABLE voters (
    voterID VARCHAR(20) PRIMARY KEY,
    voterPass VARCHAR(50) NOT NULL,
    voterFName VARCHAR(50) NOT NULL,
    voterMName VARCHAR(50),
    voterLName VARCHAR(50) NOT NULL,
    voterStat VARCHAR(10) NOT NULL DEFAULT 'Active',
    voted VARCHAR(3) NOT NULL DEFAULT 'No'
);

CREATE TABLE votes (
    posID INT NOT NULL,
    voterID VARCHAR(20) NOT NULL,
    candID INT NOT NULL
);

INSERT INTO positions (posName, numOfPositions) VALUES
    ('President', 1), ('Vice President', 1), ('Senator', 3);

INSERT INTO candidates (candFName, candLName, posID) VALUES
    ('Juan', 'Dela Cruz', 1), ('Maria', 'Santos', 1),
    ('Pedro', 'Reyes', 2), ('Ana', 'Lopez', 2),
    ('Jose', 'Rizal', 3), ('Andres', 'Bonifacio', 3),
    ('Gabriela', 'Silang', 3), ('Emilio', 'Aguinaldo', 3);

INSERT INTO voters (voterID, voterPass, voterFName, voterLName) VALUES
    ('V001', 'pass1', 'Carlo', 'Tan'),
    ('V002', 'pass2', 'Liza', 'Go'),
    ('V003', 'pass3', 'Mark', 'Uy');
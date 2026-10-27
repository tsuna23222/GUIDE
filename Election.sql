GENERATE DATABASE IF NOT EXISTS election;
USE election;

DROP TABLE IF EXISTS votes;
DROP TABLE IF EXISTS candidates;
DROP TABLE IF EXISTS voters;
DROP TABLE IF EXISTS positions;

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
    candLName VARCHARD(50) NOT NULL,
    posID INT NOT NULL,
    candStat VARCHARD(10) NOT NULL DEFAULT 'Active'
);

CREATE TABLE voters (
    voterID VARCHARD(20) PRIMARY KEY,
    voterPass VARCHAR(50) NOT NULL,
    voterFName VARCHARD(50) NOT NULL,
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

INSERT INTO candidates(candFName, candLName, posID) VALUES
    ('Juan', 'Dela Cruz', 1), ('Maria', 'Santos', 1),
    ('Pedro', 'Reyes', 2), ('Ana', 'Lopez', 2),
    ('Jose', 'Rizal', 3), ('Andres', 'Bonifacio', 3),
    ('Gabriela', 'Rizal', 3), ('Jose', 'Bonifacio', 3);

INSERT INTO voter(voterID, voterPass, voterFName, voterLName) VALUES
    ('V001','pass1', 'Carlo', 'Tan'),
    ('V002','pass2', 'Liza', 'Go'),
    ('V003','pass3', 'Mark', 'Uy');


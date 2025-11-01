
------------------------------------------------------------------------------------
-- 0. DATABASE CREATION AND SELECTION
------------------------------------------------------------------------------------
-- Check if the database exists before attempting to create it
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'TrafficAnalysis')
BEGIN
    CREATE DATABASE TrafficAnalysis;
END
GO

-- Switch the database context to the newly created database
USE TrafficAnalysis;
GO

------------------------------------------------------------------------------------
-- 1. DROPPING EXISTING TABLES
-- Drop tables in reverse order of foreign key dependencies to avoid errors
------------------------------------------------------------------------------------
IF OBJECT_ID('dbo.CITATION', 'U') IS NOT NULL DROP TABLE dbo.CITATION;
IF OBJECT_ID('dbo.SCAN', 'U') IS NOT NULL DROP TABLE dbo.SCAN;
IF OBJECT_ID('dbo.VEHICLE', 'U') IS NOT NULL DROP TABLE dbo.VEHICLE;
IF OBJECT_ID('dbo.VIOLATION', 'U') IS NOT NULL DROP TABLE dbo.VIOLATION;
IF OBJECT_ID('dbo.SPEED_LIMIT', 'U') IS NOT NULL DROP TABLE dbo.SPEED_LIMIT;
IF OBJECT_ID('dbo.CAMERA', 'U') IS NOT NULL DROP TABLE dbo.CAMERA;
IF OBJECT_ID('dbo.ROAD', 'U') IS NOT NULL DROP TABLE dbo.ROAD;
IF OBJECT_ID('dbo.DRIVER', 'U') IS NOT NULL DROP TABLE dbo.DRIVER;
GO

------------------------------------------------------------------------------------
-- 2. CREATING TABLES
------------------------------------------------------------------------------------

-- DRIVER Table
CREATE TABLE dbo.DRIVER (
    Driver_ID INT IDENTITY(1,1) PRIMARY KEY,
    National_ID VARCHAR(20) NOT NULL UNIQUE,
    First_Name VARCHAR(100),
    Last_Name VARCHAR(100),
    Date_of_Birth DATE,
    Address VARCHAR(255),
    Phone_Number VARCHAR(20),
    License_Number VARCHAR(50) UNIQUE,
    License_Issue_Date DATE,
    License_Expiry_Date DATE,
    License_Class VARCHAR(10),
    Attribute_Data VARCHAR(255), 
    Points_on_License INT DEFAULT 0
);

-- ROAD Table
CREATE TABLE dbo.ROAD (
    Road_ID INT IDENTITY(1,1) PRIMARY KEY,
    Road_Name VARCHAR(255) NOT NULL,
    Road_Type VARCHAR(50),
    Length DECIMAL(10, 2),
    Lanes INT,
    Region VARCHAR(100),
    Start_Long DECIMAL(10, 6),
    Start_Lat DECIMAL(10, 6),
    End_Long DECIMAL(10, 6),
    End_Lat DECIMAL(10, 6)
);

-- CAMERA Table (Links to ROAD)
CREATE TABLE dbo.CAMERA (
    Camera_ID INT IDENTITY(1,1) PRIMARY KEY,
    Road_ID INT NOT NULL,
    Latitude DECIMAL(10, 6),
    Longitude DECIMAL(10, 6),
    Location_Description VARCHAR(255),
    Resolution VARCHAR(50),
    Status VARCHAR(50),
    Installation_Date DATE,
    Camera_Type VARCHAR(50)
);

-- SPEED_LIMIT Table (Links to ROAD)
CREATE TABLE dbo.SPEED_LIMIT (
    Speed_Limit_ID INT IDENTITY(1,1) PRIMARY KEY,
    Road_ID INT NOT NULL,
    Vehicle_Type VARCHAR(50) NOT NULL,
    Max_Speed DECIMAL(5, 2) NOT NULL
);

-- VEHICLE Table (Links to DRIVER)
CREATE TABLE dbo.VEHICLE (
    Vehicle_ID INT IDENTITY(1,1) PRIMARY KEY,
    Driver_ID INT NOT NULL, -- Foreign Key to DRIVER
    Plate_Number VARCHAR(50) NOT NULL UNIQUE,
    Registration_State VARCHAR(50),
    Vehicle_Type VARCHAR(50),
    Model VARCHAR(100),
    Color VARCHAR(50),
    Year INT
);

-- VIOLATION Table (Lookup/Code Table)
CREATE TABLE dbo.VIOLATION (
    Violation_ID INT IDENTITY(1,1) PRIMARY KEY,
    Violation_Code VARCHAR(50) UNIQUE,
    Violation_Type VARCHAR(50),
    Description VARCHAR(MAX), -- Using VARCHAR(MAX) for 'text' field -- m3rf4 'text' dy mawgoda wla l2 fa 3mlt varchar max :)
    Points INT,
    Base_Fine DECIMAL(10, 2),
    Active_Flag BIT,
    Status VARCHAR(50)
);

-- SCAN Table (Links to VEHICLE and CAMERA)
CREATE TABLE dbo.SCAN (
    Scan_ID INT IDENTITY(1,1) PRIMARY KEY,
    Vehicle_ID INT NOT NULL, -- Foreign Key to VEHICLE
    Camera_ID INT NOT NULL,  -- Foreign Key to CAMERA
    Scan_DateTime DATETIME2 NOT NULL, 
    Lane_Number INT,
    GPS_Longitude DECIMAL(10, 6),
    GPS_Latitude DECIMAL(10, 6),
    Speed_Recorded DECIMAL(5, 2),
	Legal_Flag BIT, 
	SF_Flag BIT,
    SB_Flag BIT
);

-- CITATION Table (Links to SCAN and VIOLATION)
CREATE TABLE dbo.CITATION (
    Citation_ID INT IDENTITY(1,1) PRIMARY KEY,
    Scan_ID INT NOT NULL, -- Foreign Key to SCAN
    Violation_ID INT NOT NULL, -- Foreign Key to VIOLATION
    Citation_Date DATE NOT NULL,
    Citation_Time TIME(0) NOT NULL,
    Fine_Amount DECIMAL(10, 2),
    Late_Fee DECIMAL(10, 2),
    Total_Amount DECIMAL(10, 2),
    Payment_Due_Date DATE,
    Payment_Date DATE
);


------------------------------------------------------------------------------------
-- 3. ADDING FOREIGN KEYS
------------------------------------------------------------------------------------

-- CAMERA FK
ALTER TABLE dbo.CAMERA
ADD CONSTRAINT FK_CAMERA_ROAD
FOREIGN KEY (Road_ID) REFERENCES dbo.ROAD(Road_ID);

-- SPEED_LIMIT FK
ALTER TABLE dbo.SPEED_LIMIT
ADD CONSTRAINT FK_SPEEDLIMIT_ROAD
FOREIGN KEY (Road_ID) REFERENCES dbo.ROAD(Road_ID);

-- VEHICLE FK
ALTER TABLE dbo.VEHICLE
ADD CONSTRAINT FK_VEHICLE_DRIVER
FOREIGN KEY (Driver_ID) REFERENCES dbo.DRIVER(Driver_ID);

-- SCAN FKs
ALTER TABLE dbo.SCAN
ADD CONSTRAINT FK_SCAN_VEHICLE
FOREIGN KEY (Vehicle_ID) REFERENCES dbo.VEHICLE(Vehicle_ID);

ALTER TABLE dbo.SCAN
ADD CONSTRAINT FK_SCAN_CAMERA
FOREIGN KEY (Camera_ID) REFERENCES dbo.CAMERA(Camera_ID);

-- CITATION FKs
ALTER TABLE dbo.CITATION
ADD CONSTRAINT FK_CITATION_SCAN
FOREIGN KEY (Scan_ID) REFERENCES dbo.SCAN(Scan_ID);

ALTER TABLE dbo.CITATION
ADD CONSTRAINT FK_CITATION_VIOLATION
FOREIGN KEY (Violation_ID) REFERENCES dbo.VIOLATION(Violation_ID);

GO

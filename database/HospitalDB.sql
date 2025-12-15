/* 
    If database is not created, first do:
    CREATE DATABASE HospitalDB;
*/

USE HospitalDB;

/* ============================
   1. ROLE
   ============================ */
CREATE TABLE Role (
    RoleId          INT IDENTITY(1,1) PRIMARY KEY,
    RoleName        NVARCHAR(50) NOT NULL,
    Description     NVARCHAR(255) NULL
);
GO

/* ============================
   2. HOSPITAL
   ============================ */
CREATE TABLE Hospital (
    HospitalId      INT IDENTITY(1,1) PRIMARY KEY,
    HospitalName    NVARCHAR(100) NOT NULL,
    Address         NVARCHAR(255) NULL,
    Phone           NVARCHAR(20) NULL
);
GO

/* ============================
   3. DEPARTMENT
   ============================ */
CREATE TABLE Department (
    DepartmentId    INT IDENTITY(1,1) PRIMARY KEY,
    DepartmentName  NVARCHAR(100) NOT NULL,
    Description     NVARCHAR(255) NULL,
    HospitalId      INT NOT NULL
);
GO

/* ============================
   4. PATIENT
   ============================ */
CREATE TABLE Patient (
    PatientId       INT IDENTITY(1,1) PRIMARY KEY,
    FirstName       NVARCHAR(50) NOT NULL,
    LastName        NVARCHAR(50) NOT NULL,
    TCNo            NVARCHAR(11) NOT NULL UNIQUE,
    BirthDate       DATE NOT NULL,
    Gender          NVARCHAR(10) NULL,
    Phone           NVARCHAR(20) NULL,
    Email           NVARCHAR(100) NULL,
    Address         NVARCHAR(255) NULL,
    IsActive        BIT NOT NULL DEFAULT 1
);
GO

/* ============================
   5. STAFF
   ============================ */
CREATE TABLE Staff (
    StaffId         INT IDENTITY(1,1) PRIMARY KEY,
    FirstName       NVARCHAR(50) NOT NULL,
    LastName        NVARCHAR(50) NOT NULL,
    Title           NVARCHAR(50) NULL,
    DepartmentId    INT NOT NULL,
    Phone           NVARCHAR(20) NULL,
    Email           NVARCHAR(100) NULL,
    IsActive        BIT NOT NULL DEFAULT 1
);
GO

/* ============================
   6. USERACCOUNT
   ============================ */
CREATE TABLE UserAccount (
    UserId          INT IDENTITY(1,1) PRIMARY KEY,
    Username        NVARCHAR(50) NOT NULL UNIQUE,
    PasswordHash    NVARCHAR(255) NOT NULL,
    RoleId          INT NOT NULL,
    StaffId         INT NULL,
    PatientId       INT NULL,
    IsActive        BIT NOT NULL DEFAULT 1
);
GO

/* ============================
   7. ROOMTYPE
   ============================ */
CREATE TABLE RoomType (
    RoomTypeId      INT IDENTITY(1,1) PRIMARY KEY,
    TypeName        NVARCHAR(50) NOT NULL,
    Description     NVARCHAR(255) NULL,
    DefaultCapacity INT NOT NULL,
    BaseDailyPrice  DECIMAL(18,2) NOT NULL
);
GO

/* ============================
   8. ROOM
   ============================ */
CREATE TABLE Room (
    RoomId          INT IDENTITY(1,1) PRIMARY KEY,
    RoomNumber      NVARCHAR(20) NOT NULL,
    RoomTypeId      INT NOT NULL,
    HospitalId      INT NOT NULL,
    Floor           NVARCHAR(10) NULL,
    IsActive        BIT NOT NULL DEFAULT 1,
    DepartmentId    INT NOT NULL
);
GO

/* ============================
   9. RESERVATIONSTATUS
   ============================ */
CREATE TABLE ReservationStatus (
    StatusId        INT IDENTITY(1,1) PRIMARY KEY,
    StatusName      NVARCHAR(50) NOT NULL,
    Description     NVARCHAR(255) NULL
);
GO

/* ============================
   10. RESERVATION
   ============================ */
CREATE TABLE Reservation (
    ReservationId       INT IDENTITY(1,1) PRIMARY KEY,
    PatientId           INT NOT NULL,
    RoomId              INT NOT NULL,
    CreatedByStaffId    INT NOT NULL,
    StatusId            INT NOT NULL,
    StartDate           DATE NOT NULL,
    EndDate             DATE NOT NULL,
    CreatedDate         DATE NOT NULL DEFAULT GETDATE()
    -- İstersen CHECK (StartDate < EndDate) ekleyebilirsin:
    -- ,CONSTRAINT CK_Reservation_Dates CHECK (StartDate < EndDate)
);
GO

/* ============================
   11. SERVICECATEGORY
   ============================ */
CREATE TABLE ServiceCategory (
    ServiceCategoryId   INT IDENTITY(1,1) PRIMARY KEY,
    CategoryName        NVARCHAR(100) NOT NULL,
    Description         NVARCHAR(255) NULL
);
GO

/* ============================
   12. HEALTHSERVICE
   ============================ */
CREATE TABLE HealthService (
    ServiceId           INT IDENTITY(1,1) PRIMARY KEY,
    ServiceName         NVARCHAR(100) NOT NULL,
    ServiceCategoryId   INT NOT NULL,
    BasePrice           DECIMAL(18,2) NOT NULL
);
GO

/* ============================
   13. STATEPROGRAM
   ============================ */
CREATE TABLE StateProgram (
    ProgramId           INT IDENTITY(1,1) PRIMARY KEY,
    ProgramName         NVARCHAR(100) NOT NULL,
    Description         NVARCHAR(255) NULL,
    CoverageRate        DECIMAL(5,2) NOT NULL  -- örn: 80.00 = %80
);
GO

/* ============================
   14. SERVICERECORD
   ============================ */
CREATE TABLE ServiceRecord (
    ServiceRecordId         INT IDENTITY(1,1) PRIMARY KEY,
    PatientId               INT NOT NULL,
    ServiceId               INT NOT NULL,
    DoctorId                INT NOT NULL,
    ProgramId               INT NULL,
    ServiceDate             DATE NOT NULL,
    TotalPrice              DECIMAL(18,2) NOT NULL,
    StateCoveredAmount      DECIMAL(18,2) NOT NULL,
    PatientPayableAmount    DECIMAL(18,2) NOT NULL
);
GO

/* ============================
   15. PAYMENTTYPE
   ============================ */
CREATE TABLE PaymentType (
    PaymentTypeId       INT IDENTITY(1,1) PRIMARY KEY,
    PaymentTypeName     NVARCHAR(50) NOT NULL,
    Description         NVARCHAR(255) NULL
);
GO

/* ============================
   16. PAYMENT
   ============================ */
CREATE TABLE Payment (
    PaymentId       INT IDENTITY(1,1) PRIMARY KEY,
    ServiceRecordId INT NOT NULL,
    PaymentDate     DATE NOT NULL,
    Amount          DECIMAL(18,2) NOT NULL,
    PaymentTypeId   INT NOT NULL,
    Payer           NVARCHAR(20) NOT NULL  -- 'Patient' / 'State' gibi
);
GO

/* ==========================================
   FOREIGN KEY TANIMLARI
   ========================================== */

-- Department → Hospital
ALTER TABLE Department
ADD CONSTRAINT FK_Department_Hospital
    FOREIGN KEY (HospitalId) REFERENCES Hospital(HospitalId);
GO

-- Staff → Department
ALTER TABLE Staff
ADD CONSTRAINT FK_Staff_Department
    FOREIGN KEY (DepartmentId) REFERENCES Department(DepartmentId);
GO

-- UserAccount → Role
ALTER TABLE UserAccount
ADD CONSTRAINT FK_UserAccount_Role
    FOREIGN KEY (RoleId) REFERENCES Role(RoleId);
GO

-- UserAccount → Staff
ALTER TABLE UserAccount
ADD CONSTRAINT FK_UserAccount_Staff
    FOREIGN KEY (StaffId) REFERENCES Staff(StaffId);
GO

-- UserAccount → Patient
ALTER TABLE UserAccount
ADD CONSTRAINT FK_UserAccount_Patient
    FOREIGN KEY (PatientId) REFERENCES Patient(PatientId);
GO

-- Room → RoomType
ALTER TABLE Room
ADD CONSTRAINT FK_Room_RoomType
    FOREIGN KEY (RoomTypeId) REFERENCES RoomType(RoomTypeId);
GO

-- Room → Hospital
ALTER TABLE Room
ADD CONSTRAINT FK_Room_Hospital
    FOREIGN KEY (HospitalId) REFERENCES Hospital(HospitalId);
GO

-- Room → Department
ALTER TABLE Room
ADD CONSTRAINT FK_Room_Department
    FOREIGN KEY (DepartmentId) REFERENCES Department(DepartmentId);
GO

-- Reservation → Patient
ALTER TABLE Reservation
ADD CONSTRAINT FK_Reservation_Patient
    FOREIGN KEY (PatientId) REFERENCES Patient(PatientId);
GO

-- Reservation → Room
ALTER TABLE Reservation
ADD CONSTRAINT FK_Reservation_Room
    FOREIGN KEY (RoomId) REFERENCES Room(RoomId);
GO

-- Reservation → Staff (CreatedByStaffId)
ALTER TABLE Reservation
ADD CONSTRAINT FK_Reservation_Staff
    FOREIGN KEY (CreatedByStaffId) REFERENCES Staff(StaffId);
GO

-- Reservation → ReservationStatus
ALTER TABLE Reservation
ADD CONSTRAINT FK_Reservation_ReservationStatus
    FOREIGN KEY (StatusId) REFERENCES ReservationStatus(StatusId);
GO

-- HealthService → ServiceCategory
ALTER TABLE HealthService
ADD CONSTRAINT FK_HealthService_ServiceCategory
    FOREIGN KEY (ServiceCategoryId) REFERENCES ServiceCategory(ServiceCategoryId);
GO

-- ServiceRecord → Patient
ALTER TABLE ServiceRecord
ADD CONSTRAINT FK_ServiceRecord_Patient
    FOREIGN KEY (PatientId) REFERENCES Patient(PatientId);
GO

-- ServiceRecord → HealthService
ALTER TABLE ServiceRecord
ADD CONSTRAINT FK_ServiceRecord_HealthService
    FOREIGN KEY (ServiceId) REFERENCES HealthService(ServiceId);
GO

-- ServiceRecord → Staff (Doctor)
ALTER TABLE ServiceRecord
ADD CONSTRAINT FK_ServiceRecord_Staff_Doctor
    FOREIGN KEY (DoctorId) REFERENCES Staff(StaffId);
GO

-- ServiceRecord → StateProgram
ALTER TABLE ServiceRecord
ADD CONSTRAINT FK_ServiceRecord_StateProgram
    FOREIGN KEY (ProgramId) REFERENCES StateProgram(ProgramId);
GO

-- Payment → ServiceRecord
ALTER TABLE Payment
ADD CONSTRAINT FK_Payment_ServiceRecord
    FOREIGN KEY (ServiceRecordId) REFERENCES ServiceRecord(ServiceRecordId);
GO

-- Payment → PaymentType
ALTER TABLE Payment
ADD CONSTRAINT FK_Payment_PaymentType
    FOREIGN KEY (PaymentTypeId) REFERENCES PaymentType(PaymentTypeId);
GO
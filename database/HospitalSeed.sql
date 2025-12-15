USE HospitalDB;
GO

------------------------------------------------------------
-- 1) Clear data (child -> parent order)  [NO DROP]
------------------------------------------------------------
DELETE FROM Payment;
DELETE FROM ServiceRecord;
DELETE FROM Reservation;
DELETE FROM UserAccount;
DELETE FROM Room;
DELETE FROM Staff;
DELETE FROM Patient;
DELETE FROM HealthService;
DELETE FROM ServiceCategory;
DELETE FROM StateProgram;
DELETE FROM PaymentType;
DELETE FROM ReservationStatus;
DELETE FROM Department;
DELETE FROM Role;
DELETE FROM RoomType;
DELETE FROM Hospital;

------------------------------------------------------------
-- 2) Seed base/master tables
------------------------------------------------------------

-- Hospital
INSERT INTO Hospital (HospitalName, Address, Phone)
VALUES ('Merkez Hastanesi', 'Istanbul', '02120000000');
-- expects HospitalId = 1

-- Roles
INSERT INTO Role (RoleName, Description) VALUES
('Admin', 'System administrator'),
('Doctor', 'Medical doctor'),
('Receptionist', 'Front desk staff');
-- expects RoleId: 1=Admin, 2=Doctor, 3=Receptionist

-- Departments
INSERT INTO Department (DepartmentName, Description, HospitalId) VALUES
('Genel Servis', 'General services', 1),
('Dahiliye', 'Internal medicine', 1);
-- expects DepartmentId: 1,2

-- Staff
INSERT INTO Staff (FirstName, LastName, Title, DepartmentId, Phone, Email, IsActive) VALUES
('Ali',    'Yilmaz', 'Admin',        1, '5551112233', 'ali.admin@hospital.com', 1),
('Ayse',   'Demir',  'Doctor',       2, '5552223344', 'ayse.dr@hospital.com',   1),
('Mehmet', 'Kaya',   'Receptionist', 1, '5553334455', 'mehmet.rec@hospital.com',1);
-- expects StaffId: 1=Ali, 2=Ayse, 3=Mehmet

-- RoomType
INSERT INTO RoomType (TypeName, Description, DefaultCapacity, BaseDailyPrice) VALUES
('Standard', 'Standard room', 2, 1500),
('Deluxe',   'Deluxe room',   1, 2500);
-- expects RoomTypeId: 1,2

-- Rooms (Room -> HospitalId + RoomTypeId + DepartmentId required)
INSERT INTO Room (RoomNumber, RoomTypeId, HospitalId, Floor, IsActive, DepartmentId) VALUES
('101', 1, 1, '1', 1, 1),
('102', 1, 1, '1', 1, 1),
('201', 2, 1, '2', 1, 2),
('202', 2, 1, '2', 1, 2);
-- expects RoomId: 1..4

-- Reservation Statuses
INSERT INTO ReservationStatus (StatusName, Description) VALUES
('Reserved',  'Booked, not checked in'),
('CheckedIn', 'Patient checked in'),
('Cancelled', 'Reservation cancelled');
-- expects StatusId: 1,2,3

-- Payment Types
INSERT INTO PaymentType (PaymentTypeName, Description) VALUES
('Cash', 'Nakit'),
('Card', 'Kredi Kartı'),
('Transfer', 'Havale/EFT');
-- expects PaymentTypeId: 1..3

-- State Programs (CoverageRate as fraction: 0.80 = %80)
INSERT INTO StateProgram (ProgramName, Description, CoverageRate) VALUES
('SGK',  'Devlet kapsamı', 0.80),
('None', 'Kapsam yok',     0.00);
-- expects ProgramId: 1=SGK, 2=None

-- Service Categories
INSERT INTO ServiceCategory (CategoryName, Description) VALUES
('Muayene',     'Poliklinik muayene'),
('Laboratuvar', 'Lab testleri'),
('Goruntuleme', 'Radyoloji / MR / BT');
-- expects ServiceCategoryId: 1..3

-- Health Services
INSERT INTO HealthService (ServiceName, ServiceCategoryId, BasePrice) VALUES
('Dahiliye Muayene', 1, 500),
('Kan Testi',        2, 300),
('MR Cekimi',        3, 1200);
-- expects ServiceId: 1..3

------------------------------------------------------------
-- 3) Seed operational tables
------------------------------------------------------------

-- Patients
INSERT INTO Patient
(FirstName, LastName, TCNo, BirthDate, Gender, Phone, Email, Address, IsActive)
VALUES
('Omer', 'Zorlu', '11111111111', '2001-01-01', 'Male',   '5554445566', 'omer@demo.com', 'Istanbul', 1),
('Ece',  'Kaya',  '22222222222', '1999-05-12', 'Female', '5557778899', 'ece@demo.com',  'Istanbul', 1);
-- expects PatientId: 1..2

-- User Accounts (login-only)
INSERT INTO UserAccount (Username, PasswordHash, RoleId, StaffId, PatientId, IsActive) VALUES
('admin',     '1234', 1, 1, NULL, 1),
('doctor',    '1234', 2, 2, NULL, 1),
('reception', '1234', 3, 3, NULL, 1);

-- Reservations (CreatedByStaffId required)
INSERT INTO Reservation
(PatientId, RoomId, CreatedByStaffId, StatusId, StartDate, EndDate, CreatedDate)
VALUES
(1, 3, 3, 1, '2025-01-10', '2025-01-12', CAST(GETDATE() AS date)),
(2, 1, 3, 1, '2025-01-15', '2025-01-16', CAST(GETDATE() AS date));

-- ServiceRecords (DoctorId = StaffId of doctor -> 2)
-- For Patient 1: service 1, SGK 80%
INSERT INTO ServiceRecord
(PatientId, ServiceId, DoctorId, ProgramId, ServiceDate, TotalPrice, StateCoveredAmount, PatientPayableAmount)
VALUES
(1, 1, 2, 1, CAST(GETDATE() AS date), 500.00, 400.00, 100.00),
(2, 2, 2, 2, CAST(GETDATE() AS date), 300.00,   0.00, 300.00);

-- Payments (ServiceRecordId assumed 1..2)
INSERT INTO Payment
(ServiceRecordId, PaymentDate, Amount, PaymentTypeId, Payer)
VALUES
(1, CAST(GETDATE() AS date), 100.00, 2, 'Patient'),
(2, CAST(GETDATE() AS date), 300.00, 1, 'Patient');
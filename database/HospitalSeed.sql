USE HospitalDB;
GO

SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRAN;

    ------------------------------------------------------------
    -- 1) Disable FK checks temporarily (so we can delete safely)
    ------------------------------------------------------------
    ALTER TABLE dbo.payment           NOCHECK CONSTRAINT ALL;
    ALTER TABLE dbo.servicerecord     NOCHECK CONSTRAINT ALL;
    ALTER TABLE dbo.reservation       NOCHECK CONSTRAINT ALL;
    ALTER TABLE dbo.useraccount       NOCHECK CONSTRAINT ALL;
    ALTER TABLE dbo.room              NOCHECK CONSTRAINT ALL;
    ALTER TABLE dbo.staff             NOCHECK CONSTRAINT ALL;
    ALTER TABLE dbo.department        NOCHECK CONSTRAINT ALL;
    ALTER TABLE dbo.healthservice     NOCHECK CONSTRAINT ALL;
    ALTER TABLE dbo.servicecategory   NOCHECK CONSTRAINT ALL;
    ALTER TABLE dbo.stateprogram      NOCHECK CONSTRAINT ALL;
    ALTER TABLE dbo.paymenttype       NOCHECK CONSTRAINT ALL;
    ALTER TABLE dbo.reservationstatus NOCHECK CONSTRAINT ALL;
    ALTER TABLE dbo.patient           NOCHECK CONSTRAINT ALL;
    ALTER TABLE dbo.role              NOCHECK CONSTRAINT ALL;
    ALTER TABLE dbo.roomtype          NOCHECK CONSTRAINT ALL;
    ALTER TABLE dbo.hospital          NOCHECK CONSTRAINT ALL;

    ------------------------------------------------------------
    -- 2) Delete rows in safe order (children -> parents)
    --    (No DROP, only clearing data)
    ------------------------------------------------------------
    DELETE FROM dbo.payment;
    DELETE FROM dbo.servicerecord;
    DELETE FROM dbo.reservation;
    DELETE FROM dbo.useraccount;
    DELETE FROM dbo.room;
    DELETE FROM dbo.staff;
    DELETE FROM dbo.department;
    DELETE FROM dbo.healthservice;
    DELETE FROM dbo.servicecategory;
    DELETE FROM dbo.stateprogram;
    DELETE FROM dbo.paymenttype;
    DELETE FROM dbo.reservationstatus;
    DELETE FROM dbo.patient;
    DELETE FROM dbo.role;
    DELETE FROM dbo.roomtype;
    DELETE FROM dbo.hospital;

    ------------------------------------------------------------
    -- 3) Reseed identity columns (if they are IDENTITY)
    --    If a table isn't identity, CHECKIDENT will error,
    --    so we guard with TRY...CATCH per table.
    ------------------------------------------------------------
    DECLARE @t TABLE (name sysname);
    INSERT INTO @t(name) VALUES
      ('payment'), ('servicerecord'), ('reservation'), ('useraccount'),
      ('room'), ('staff'), ('department'), ('healthservice'),
      ('servicecategory'), ('stateprogram'), ('paymenttype'),
      ('reservationstatus'), ('patient'), ('role'), ('roomtype'), ('hospital');

    DECLARE @name sysname;
    DECLARE cur CURSOR FOR SELECT name FROM @t;
    OPEN cur;
    FETCH NEXT FROM cur INTO @name;
    WHILE @@FETCH_STATUS = 0
    BEGIN
        BEGIN TRY
            EXEC('DBCC CHECKIDENT (''dbo.' + @name + ''', RESEED, 0);');
        END TRY
        BEGIN CATCH
            -- ignore if not identity
        END CATCH;

        FETCH NEXT FROM cur INTO @name;
    END
    CLOSE cur;
    DEALLOCATE cur;

    ------------------------------------------------------------
    -- 4) Seed master tables first
    ------------------------------------------------------------
    DECLARE @HospitalId int;

    INSERT INTO dbo.hospital (HospitalName, Address, Phone)
    VALUES ('Merkez Hastanesi', 'Istanbul', '02120000000');
    SET @HospitalId = SCOPE_IDENTITY();

    -- Roles
    DECLARE @RoleAdmin int, @RoleDoctor int, @RoleReception int;

    INSERT INTO dbo.role (RoleName, Description) VALUES
      ('Admin', 'System administrator'),
      ('Doctor', 'Medical doctor'),
      ('Receptionist', 'Front desk / registration');

    SELECT @RoleAdmin = RoleId FROM dbo.role WHERE RoleName='Admin';
    SELECT @RoleDoctor = RoleId FROM dbo.role WHERE RoleName='Doctor';
    SELECT @RoleReception = RoleId FROM dbo.role WHERE RoleName='Receptionist';

    -- Departments
    DECLARE @DeptGenel int, @DeptDahiliye int;

    INSERT INTO dbo.department (DepartmentName, Description, HospitalId)
    VALUES
      ('Genel Servis', 'Genel yat�� servisi', @HospitalId),
      ('Dahiliye', 'Dahiliye servisi', @HospitalId);

    SELECT @DeptGenel = DepartmentId FROM dbo.department WHERE DepartmentName='Genel Servis';
    SELECT @DeptDahiliye = DepartmentId FROM dbo.department WHERE DepartmentName='Dahiliye';

    -- Staff
    DECLARE @StaffAdmin int, @StaffDoctor int, @StaffReception int;

    INSERT INTO dbo.staff (FirstName, LastName, Title, DepartmentId, Phone, Email, IsActive)
    VALUES
      ('Ali',  'Yilmaz', 'Admin',        @DeptGenel,    '5551112233', 'ali.admin@hospital.com', 1),
      ('Ayse', 'Demir',  'Doctor',       @DeptDahiliye, '5552223344', 'ayse.dr@hospital.com',   1),
      ('Mehmet','Kaya',  'Receptionist', @DeptGenel,    '5553334455', 'mehmet.rec@hospital.com',1);

    SELECT @StaffAdmin = StaffId FROM dbo.staff WHERE Email='ali.admin@hospital.com';
    SELECT @StaffDoctor = StaffId FROM dbo.staff WHERE Email='ayse.dr@hospital.com';
    SELECT @StaffReception = StaffId FROM dbo.staff WHERE Email='mehmet.rec@hospital.com';

    -- Room types
    DECLARE @RTStandard int, @RTDeluxe int;

    INSERT INTO dbo.roomtype (TypeName, Description, DefaultCapacity, BaseDailyPrice)
    VALUES
      ('Standard', 'Standard room', 2, 1500),
      ('Deluxe',   'Deluxe room',   1, 2500);

    SELECT @RTStandard = RoomTypeId FROM dbo.roomtype WHERE TypeName='Standard';
    SELECT @RTDeluxe   = RoomTypeId FROM dbo.roomtype WHERE TypeName='Deluxe';

    -- Rooms
    DECLARE @Room101 int, @Room201 int;

    INSERT INTO dbo.room (RoomNumber, RoomTypeId, HospitalId, Floor, IsActive, DepartmentId)
    VALUES
      ('101', @RTStandard, @HospitalId, '1', 1, @DeptGenel),
      ('201', @RTDeluxe,   @HospitalId, '2', 1, @DeptDahiliye);

    SELECT @Room101 = RoomId FROM dbo.room WHERE RoomNumber='101';
    SELECT @Room201 = RoomId FROM dbo.room WHERE RoomNumber='201';

    -- Reservation statuses
    DECLARE @StReserved int, @StCheckedIn int, @StCancelled int;

    INSERT INTO dbo.reservationstatus (StatusName, Description)
    VALUES
      ('Reserved',  'Booked, not checked in'),
      ('CheckedIn', 'Patient checked in'),
      ('Cancelled', 'Reservation cancelled');

    SELECT @StReserved  = StatusId FROM dbo.reservationstatus WHERE StatusName='Reserved';
    SELECT @StCheckedIn = StatusId FROM dbo.reservationstatus WHERE StatusName='CheckedIn';
    SELECT @StCancelled = StatusId FROM dbo.reservationstatus WHERE StatusName='Cancelled';

    -- Service categories
    DECLARE @CatMuayene int, @CatLab int;

    INSERT INTO dbo.servicecategory (CategoryName, Description)
    VALUES
      ('Muayene', 'Poliklinik muayene'),
      ('Laboratuvar', 'Lab testleri');

    SELECT @CatMuayene = ServiceCategoryId FROM dbo.servicecategory WHERE CategoryName='Muayene';
    SELECT @CatLab     = ServiceCategoryId FROM dbo.servicecategory WHERE CategoryName='Laboratuvar';

    -- Health services
    DECLARE @SrvDahiliye int, @SrvKanTest int;

    INSERT INTO dbo.healthservice (ServiceName, ServiceCategoryId, BasePrice)
    VALUES
      ('Dahiliye Muayene', @CatMuayene, 500),
      ('Kan Testi',        @CatLab,     300);

    SELECT @SrvDahiliye = ServiceId FROM dbo.healthservice WHERE ServiceName='Dahiliye Muayene';
    SELECT @SrvKanTest  = ServiceId FROM dbo.healthservice WHERE ServiceName='Kan Testi';

    -- State programs (CoverageRate is decimal fraction like 0.80)
    DECLARE @ProgSGK int, @ProgNone int;

    INSERT INTO dbo.stateprogram (ProgramName, Description, CoverageRate)
    VALUES
      ('SGK',  'Devlet kapsam�', 0.80),
      ('None', 'Kapsam yok',     0.00);

    SELECT @ProgSGK  = ProgramId FROM dbo.stateprogram WHERE ProgramName='SGK';
    SELECT @ProgNone = ProgramId FROM dbo.stateprogram WHERE ProgramName='None';

    -- Payment types
    DECLARE @PayCash int, @PayCard int;

    INSERT INTO dbo.paymenttype (PaymentTypeName, Description)
    VALUES
      ('Cash', 'Nakit �deme'),
      ('Card', 'Kredi kart�');

    SELECT @PayCash = PaymentTypeId FROM dbo.paymenttype WHERE PaymentTypeName='Cash';
    SELECT @PayCard = PaymentTypeId FROM dbo.paymenttype WHERE PaymentTypeName='Card';

    ------------------------------------------------------------
    -- 5) Seed patients
    ------------------------------------------------------------
    DECLARE @Patient1 int, @Patient2 int;

    INSERT INTO dbo.patient
      (FirstName, LastName, TCNo, BirthDate, Gender, Phone, Email, Address, IsActive)
    VALUES
      ('Omer', 'Zorlu', '11111111111', '2001-01-01', 'Male',   '5554445566', 'oz@zorlu.com', 'Istanbul', 1),
      ('Ece',  'Kaya',  '22222222222', '1999-05-12', 'Female', '5557778899', 'ece@kaya.com', 'Istanbul', 1);

    SELECT @Patient1 = PatientId FROM dbo.patient WHERE TCNo='11111111111';
    SELECT @Patient2 = PatientId FROM dbo.patient WHERE TCNo='22222222222';

    ------------------------------------------------------------
    -- 6) Seed user accounts (no signup, default passwords)
    ------------------------------------------------------------
    INSERT INTO dbo.useraccount (Username, PasswordHash, RoleId, StaffId, PatientId, IsActive)
    VALUES
      ('admin',     '1234', @RoleAdmin,      @StaffAdmin,      NULL, 1),
      ('doctor',    '1234', @RoleDoctor,     @StaffDoctor,     NULL, 1),
      ('reception', '1234', @RoleReception,  @StaffReception,  NULL, 1);

    ------------------------------------------------------------
    -- 7) Seed a reservation
    ------------------------------------------------------------
    DECLARE @Res1 int;

    INSERT INTO dbo.reservation
      (PatientId, RoomId, CreatedByStaffId, StatusId, StartDate, EndDate, CreatedDate)
    VALUES
      (@Patient1, @Room201, @StaffReception, @StReserved, '2025-01-10', '2025-01-12', CAST(GETDATE() AS date));

    SET @Res1 = SCOPE_IDENTITY();

    ------------------------------------------------------------
    -- 8) Seed a service record + payment
    ------------------------------------------------------------
    DECLARE @SR1 int;

    DECLARE @Total decimal(18,2) = 500.00;
    DECLARE @Covered decimal(18,2) = @Total * 0.80;
    DECLARE @Payable decimal(18,2) = @Total - @Covered;

    INSERT INTO dbo.servicerecord
      (PatientId, ServiceId, DoctorId, ProgramId, ServiceDate, TotalPrice, StateCoveredAmount, PatientPayableAmount)
    VALUES
      (@Patient1, @SrvDahiliye, @StaffDoctor, @ProgSGK, CAST(GETDATE() AS date), @Total, @Covered, @Payable);

    SET @SR1 = SCOPE_IDENTITY();

    INSERT INTO dbo.payment
      (ServiceRecordId, PaymentDate, Amount, PaymentTypeId, Payer)
    VALUES
      (@SR1, CAST(GETDATE() AS date), @Payable, @PayCard, 'Patient');

    ------------------------------------------------------------
    -- 9) Re-enable constraints
    ------------------------------------------------------------
    ALTER TABLE dbo.hospital          CHECK CONSTRAINT ALL;
    ALTER TABLE dbo.roomtype          CHECK CONSTRAINT ALL;
    ALTER TABLE dbo.role              CHECK CONSTRAINT ALL;
    ALTER TABLE dbo.patient           CHECK CONSTRAINT ALL;
    ALTER TABLE dbo.reservationstatus CHECK CONSTRAINT ALL;
    ALTER TABLE dbo.paymenttype       CHECK CONSTRAINT ALL;
    ALTER TABLE dbo.stateprogram      CHECK CONSTRAINT ALL;
    ALTER TABLE dbo.servicecategory   CHECK CONSTRAINT ALL;
    ALTER TABLE dbo.healthservice     CHECK CONSTRAINT ALL;
    ALTER TABLE dbo.department        CHECK CONSTRAINT ALL;
    ALTER TABLE dbo.staff             CHECK CONSTRAINT ALL;
    ALTER TABLE dbo.room              CHECK CONSTRAINT ALL;
    ALTER TABLE dbo.useraccount       CHECK CONSTRAINT ALL;
    ALTER TABLE dbo.reservation       CHECK CONSTRAINT ALL;
    ALTER TABLE dbo.servicerecord     CHECK CONSTRAINT ALL;
    ALTER TABLE dbo.payment           CHECK CONSTRAINT ALL;

    COMMIT;

    PRINT 'Seed completed successfully. Try login: admin/1234, doctor/1234, reception/1234';
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK;
    DECLARE @msg nvarchar(max) = ERROR_MESSAGE();
    PRINT 'Seed failed: ' + @msg;
    THROW;
END CATCH
GO
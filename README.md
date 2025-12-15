# 🏥 Hospital Management System

## 📌 Project Overview

This project is a **Hospital Management System** developed using **Python (PyQt6)** for the graphical user interface and **Microsoft SQL Server** for the database.

The system is **role-based** and designed according to real-world hospital workflows.  
There is **no signup functionality**; all user accounts are created and managed by the **Admin**.

---

## 🧱 Technologies Used

- **Python 3**
- **PyQt6** – Desktop GUI
- **SQLAlchemy (Core)** – Database access
- **pyodbc** – MS SQL Server driver
- **Microsoft SQL Server**
- **Conda Environment**

---

## 👥 User Roles & Permissions

### 👑 Admin
- Manage user accounts (add, edit, deactivate)
- Assign roles to users
- Manage system definitions:
  - Department
  - RoomType
  - Room
  - ServiceCategory
  - HealthService
  - StateProgram
  - PaymentType
- View all reservations, service records, and payments
- Add and delete payments
- Logout to login screen

### 🩺 Doctor
- Login with assigned staff account
- View **only own** service records
- Add new service records
- Edit service records (e.g. price correction)
- Automatic calculation of:
  - State covered amount
  - Patient payable amount
- Logout to login screen

### 🧾 Receptionist
- Create and update patient records
- Create and update room reservations
- Check room availability
- Reservation records include:
  - CreatedByStaffId
  - CreatedDate
- Logout to login screen

---

## 🔐 Authentication Rules

- Login-only system (no signup)
- User accounts are created by the Admin
- Each user account is linked to:
  - **Staff** for Admin / Doctor / Receptionist
  - *(Optional)* **Patient** for future extensions

---

## 🗄️ Database Design

- Fully normalized relational database
- Strong foreign key relationships
- Uses `IsActive` fields instead of hard deletes
- Designed for extensibility and real-world workflows

---

## ⚙️ Setup Instructions

### 1️⃣ Create Conda Environment
```bash
conda create -n hospital python=3.11
conda activate hospital
```

### 2️⃣ Install Dependencies
```
pip install -r requirements.txt
```

### 3️⃣ Configure Database Connection
Create a .env file in the project root:
```
DB_SERVER=localhost
DB_NAME=HospitalDB
DB_USER=sa
DB_PASSWORD=your_password
```

### 4️⃣ Create and Seed the Database
Run the SQL script in SQL Server Management Studio:
```
HospitalDB.sql
HospitalSeed.sql
```

### 5️⃣ Run the Application
```
python app.py
```
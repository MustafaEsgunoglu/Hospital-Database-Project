from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHBoxLayout, QMessageBox,
    QTabWidget
)
from PyQt6.QtCore import Qt
from sqlalchemy import text
from db import get_engine

from ui.user_dialog import UserDialog
from ui.staff_dialog import StaffDialog
from ui.payment_dialog import PaymentDialog
from ui.generic_crud import GenericCrudWidget, FieldSpec

engine = get_engine()

class AdminWindow(QMainWindow):
    def __init__(self, session, on_logout):
        super().__init__()
        self.session = session
        self.on_logout = on_logout
        self.setWindowTitle("Admin Panel")
        self.resize(980, 560)

        self.roles = self.load_roles()

        root = QWidget()
        layout = QVBoxLayout()

        top = QHBoxLayout()
        top.addWidget(QLabel(f"ADMIN | UserId={session['user_id']}"))
        top.addStretch(1)
        btn_logout = QPushButton("Logout (Back to Login)")
        btn_logout.clicked.connect(self._logout)
        top.addWidget(btn_logout)
        layout.addLayout(top)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_users_tab(), "UserAccount Management")
        self.tabs.addTab(self._build_staff_tab(), "Staff Management")
        self.tabs.addTab(self._build_payments_tab(), "Payments")
        self.tabs.addTab(self._build_definitions_tab(), "System Definitions")
        layout.addWidget(self.tabs)

        root.setLayout(layout)
        self.setCentralWidget(root)

        self.refresh_users()
        self.refresh_staff()
        self.refresh_payments()

    def _logout(self):
        self.close()
        self.on_logout()

    # ---------------- Common helpers ----------------
    def load_roles(self):
        q = text("SELECT RoleId, RoleName FROM Role ORDER BY RoleId")
        with engine.connect() as conn:
            return list(conn.execute(q).mappings().all())

    def load_departments(self):
        q = text("SELECT DepartmentId, DepartmentName FROM Department ORDER BY DepartmentId")
        with engine.connect() as conn:
            return list(conn.execute(q).mappings().all())

    def load_staff_list(self):
        q = text("""
            SELECT StaffId,
                   (FirstName + ' ' + LastName) AS FullName,
                   Title
            FROM Staff
            WHERE IsActive = 1 OR IsActive IS NULL
            ORDER BY StaffId
        """)
        with engine.connect() as conn:
            return list(conn.execute(q).mappings().all())

    def load_patient_list(self):
        q = text("""
            SELECT PatientId,
                   (FirstName + ' ' + LastName) AS FullName
            FROM Patient
            WHERE IsActive = 1 OR IsActive IS NULL
            ORDER BY PatientId
        """)
        with engine.connect() as conn:
            return list(conn.execute(q).mappings().all())

    def _to_int_bool(self, s: str) -> int:
        v = (s or "").strip().lower()
        if v in ("1", "true", "yes"):
            return 1
        if v in ("0", "false", "no"):
            return 0
        return 0

    def _to_int_or_none(self, s: str):
        v = (s or "").strip()
        if not v:
            return None
        try:
            return int(v)
        except ValueError:
            return None
        
    def load_payment_types(self):
        q = text("SELECT PaymentTypeId, PaymentTypeName FROM PaymentType ORDER BY PaymentTypeId")
        with engine.connect() as conn:
            return list(conn.execute(q).mappings().all())

    def load_service_records_for_payment(self):
        q = text("""
            SELECT sr.ServiceRecordId,
                ('SR#' + CAST(sr.ServiceRecordId AS varchar(20)) + ' | PatientId='
                    + CAST(sr.PatientId AS varchar(20)) + ' | DoctorId=' + CAST(sr.DoctorId AS varchar(20))
                    + ' | Payable=' + CAST(sr.PatientPayableAmount AS varchar(50))
                ) AS Display
            FROM ServiceRecord sr
            ORDER BY sr.ServiceRecordId DESC
        """)
        with engine.connect() as conn:
            return list(conn.execute(q).mappings().all())

    def refresh_payments(self):
        q = text("""
            SELECT p.PaymentId, p.ServiceRecordId, CAST(p.PaymentDate AS date) AS PaymentDate,
                p.Amount, pt.PaymentTypeName, p.Payer
            FROM Payment p
            JOIN PaymentType pt ON pt.PaymentTypeId = p.PaymentTypeId
            ORDER BY p.PaymentId DESC
        """)
        with engine.connect() as conn:
            rows = list(conn.execute(q).mappings().all())

        self.tbl_pay.setRowCount(0)
        for r in rows:
            i = self.tbl_pay.rowCount()
            self.tbl_pay.insertRow(i)

            def put(col, val, center=False):
                item = QTableWidgetItem("" if val is None else str(val))
                if center:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tbl_pay.setItem(i, col, item)

            put(0, r["PaymentId"], True)
            put(1, r["ServiceRecordId"], True)
            put(2, str(r["PaymentDate"]))
            put(3, r["Amount"], True)
            put(4, r["PaymentTypeName"])
            put(5, r["Payer"])

        self.tbl_pay.resizeColumnsToContents()

    def _selected_payment(self):
        items = self.tbl_pay.selectedItems()
        if not items:
            return None
        row = items[0].row()
        pid = self.tbl_pay.item(row, 0).text()
        return int(pid)

    def add_payment(self):
        payment_types = self.load_payment_types()
        service_records = self.load_service_records_for_payment()

        if not payment_types:
            QMessageBox.warning(self, "Info", "No PaymentType found. Add PaymentType first.")
            return
        if not service_records:
            QMessageBox.warning(self, "Info", "No ServiceRecord found. Doctor must create ServiceRecords first.")
            return

        dlg = PaymentDialog(servicerecords=service_records, payment_types=payment_types, parent=self)
        if dlg.exec() != dlg.DialogCode.Accepted:
            return
        data = dlg.get_data()

        q = text("""
            INSERT INTO Payment (ServiceRecordId, PaymentDate, Amount, PaymentTypeId, Payer)
            VALUES (:sr, :dt, :amt, :pt, :payer)
        """)
        try:
            with engine.begin() as conn:
                conn.execute(q, {
                    "sr": data["ServiceRecordId"],
                    "dt": data["PaymentDate"],
                    "amt": data["Amount"],
                    "pt": data["PaymentTypeId"],
                    "payer": data["Payer"],
                })
        except Exception as e:
            QMessageBox.critical(self, "DB Error", f"Insert failed:\n{e}")
            return

        self.refresh_payments()

    def delete_payment_hard(self):
        pid = self._selected_payment()
        if not pid:
            QMessageBox.information(self, "Info", "Select a payment first.")
            return

        ok = QMessageBox.question(
            self, "Confirm Delete",
            f"Hard delete PaymentId={pid} ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if ok != QMessageBox.StandardButton.Yes:
            return

        q = text("DELETE FROM Payment WHERE PaymentId=:id")
        try:
            with engine.begin() as conn:
                conn.execute(q, {"id": pid})
        except Exception as e:
            QMessageBox.critical(self, "DB Error", f"Delete failed:\n{e}")
            return

        self.refresh_payments()

    def load_hospitals(self):
        q = text("SELECT HospitalId AS id, HospitalName AS name FROM Hospital ORDER BY HospitalId")
        with engine.connect() as conn:
            return list(conn.execute(q).mappings().all())

    def load_departments_fk(self):
        q = text("SELECT DepartmentId AS id, DepartmentName AS name FROM Department ORDER BY DepartmentId")
        with engine.connect() as conn:
            return list(conn.execute(q).mappings().all())

    def load_service_categories_fk(self):
        q = text("SELECT ServiceCategoryId AS id, CategoryName AS name FROM ServiceCategory ORDER BY ServiceCategoryId")
        with engine.connect() as conn:
            return list(conn.execute(q).mappings().all())


    # ================= USERS TAB =================
    def _build_users_tab(self):
        w = QWidget()
        layout = QVBoxLayout()

        btns = QHBoxLayout()
        self.btn_u_refresh = QPushButton("Refresh")
        self.btn_u_add = QPushButton("Add User")
        self.btn_u_edit = QPushButton("Edit Selected")
        self.btn_u_toggle = QPushButton("Toggle Active")
        self.btn_u_delete = QPushButton("Delete (Hard)")

        self.btn_u_refresh.clicked.connect(self.refresh_users)
        self.btn_u_add.clicked.connect(self.add_user)
        self.btn_u_edit.clicked.connect(self.edit_user)
        self.btn_u_toggle.clicked.connect(self.toggle_user_active)
        self.btn_u_delete.clicked.connect(self.delete_user_hard)

        for b in [self.btn_u_refresh, self.btn_u_add, self.btn_u_edit, self.btn_u_toggle, self.btn_u_delete]:
            btns.addWidget(b)
        btns.addStretch(1)
        note_lbl = QLabel("Not: 'Toggle Active' önerilen. Hard delete FK yüzünden hata verebilir.")
        btns.addWidget(note_lbl)

        layout.addLayout(btns)

        self.tbl_users = QTableWidget(0, 8)
        self.tbl_users.setHorizontalHeaderLabels([
            "UserId", "Username", "RoleId", "RoleName", "StaffId", "PatientId", "IsActive", "PasswordHash"
        ])
        self.tbl_users.setColumnHidden(7, True)
        self.tbl_users.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl_users.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl_users.verticalHeader().setVisible(False)

        layout.addWidget(self.tbl_users)
        w.setLayout(layout)
        return w

    def refresh_users(self):
        q = text("""
            SELECT ua.UserId, ua.Username, ua.RoleId, r.RoleName,
                   ua.StaffId, ua.PatientId, ua.IsActive, ua.PasswordHash
            FROM UserAccount ua
            JOIN Role r ON r.RoleId = ua.RoleId
            ORDER BY ua.UserId
        """)
        with engine.connect() as conn:
            rows = list(conn.execute(q).mappings().all())

        self.tbl_users.setRowCount(0)
        for r in rows:
            row_idx = self.tbl_users.rowCount()
            self.tbl_users.insertRow(row_idx)

            def put(col, val, center=False):
                item = QTableWidgetItem("" if val is None else str(val))
                if center:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tbl_users.setItem(row_idx, col, item)

            put(0, r["UserId"], True)
            put(1, r["Username"])
            put(2, r["RoleId"], True)
            put(3, r["RoleName"])
            put(4, r["StaffId"], True)
            put(5, r["PatientId"], True)
            put(6, 1 if r["IsActive"] else 0, True)
            put(7, r["PasswordHash"])

        self.tbl_users.resizeColumnsToContents()

    def _selected_user(self):
        items = self.tbl_users.selectedItems()
        if not items:
            return None
        row = items[0].row()

        def get(col):
            it = self.tbl_users.item(row, col)
            return it.text() if it else ""

        return {
            "UserId": int(get(0)),
            "Username": get(1),
            "RoleId": int(get(2)) if get(2).strip() else None,
            "RoleName": get(3),
            "StaffId": self._to_int_or_none(get(4)),
            "PatientId": self._to_int_or_none(get(5)),
            "IsActive": self._to_int_bool(get(6)),
        }

    def add_user(self):
        staff_list = self.load_staff_list()
        patient_list = self.load_patient_list()
        dlg = UserDialog(mode="add", roles=self.roles, staff_list=staff_list, patient_list=patient_list, parent=self)
        if dlg.exec() != dlg.DialogCode.Accepted:
            return
        data = dlg.get_data()

        q = text("""
            INSERT INTO UserAccount (Username, PasswordHash, RoleId, StaffId, PatientId, IsActive)
            VALUES (:u, :p, :rid, :sid, :pid, :act)
        """)
        try:
            with engine.begin() as conn:
                conn.execute(q, {
                    "u": data["Username"],
                    "p": data["Password"],
                    "rid": data["RoleId"],
                    "sid": data["StaffId"],
                    "pid": data["PatientId"],
                    "act": data["IsActive"],
                })
        except Exception as e:
            QMessageBox.critical(self, "DB Error", f"Insert failed:\n{e}")
            return

        self.refresh_users()

    def edit_user(self):
        selected = self._selected_user()
        if not selected:
            QMessageBox.information(self, "Info", "Select a user row first.")
            return

        staff_list = self.load_staff_list()
        patient_list = self.load_patient_list()
        dlg = UserDialog(mode="edit", roles=self.roles, staff_list=staff_list, patient_list=patient_list,
                         initial=selected, parent=self)
        if dlg.exec() != dlg.DialogCode.Accepted:
            return
        data = dlg.get_data()

        if data["Password"]:
            q = text("""
                UPDATE UserAccount
                SET Username=:u, PasswordHash=:p, RoleId=:rid, StaffId=:sid, PatientId=:pid, IsActive=:act
                WHERE UserId=:id
            """)
            params = {
                "id": selected["UserId"],
                "u": data["Username"],
                "p": data["Password"],
                "rid": data["RoleId"],
                "sid": data["StaffId"],
                "pid": data["PatientId"],
                "act": data["IsActive"],
            }
        else:
            q = text("""
                UPDATE UserAccount
                SET Username=:u, RoleId=:rid, StaffId=:sid, PatientId=:pid, IsActive=:act
                WHERE UserId=:id
            """)
            params = {
                "id": selected["UserId"],
                "u": data["Username"],
                "rid": data["RoleId"],
                "sid": data["StaffId"],
                "pid": data["PatientId"],
                "act": data["IsActive"],
            }

        try:
            with engine.begin() as conn:
                conn.execute(q, params)
        except Exception as e:
            QMessageBox.critical(self, "DB Error", f"Update failed:\n{e}")
            return

        self.refresh_users()

    def toggle_user_active(self):
        selected = self._selected_user()
        if not selected:
            QMessageBox.information(self, "Info", "Select a user row first.")
            return

        new_val = 0 if selected["IsActive"] == 1 else 1
        q = text("UPDATE UserAccount SET IsActive=:a WHERE UserId=:id")

        try:
            with engine.begin() as conn:
                conn.execute(q, {"a": new_val, "id": selected["UserId"]})
        except Exception as e:
            QMessageBox.critical(self, "DB Error", f"Toggle failed:\n{e}")
            return

        self.refresh_users()

    def delete_user_hard(self):
        selected = self._selected_user()
        if not selected:
            QMessageBox.information(self, "Info", "Select a user row first.")
            return

        ok = QMessageBox.question(
            self, "Confirm Delete",
            f"Hard delete UserId={selected['UserId']} ?\nFK varsa hata verebilir.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if ok != QMessageBox.StandardButton.Yes:
            return

        q = text("DELETE FROM UserAccount WHERE UserId=:id")
        try:
            with engine.begin() as conn:
                conn.execute(q, {"id": selected["UserId"]})
        except Exception as e:
            QMessageBox.critical(self, "DB Error", f"Delete failed:\n{e}")
            return

        self.refresh_users()

    # ================= STAFF TAB =================
    def _build_staff_tab(self):
        w = QWidget()
        layout = QVBoxLayout()

        btns = QHBoxLayout()
        self.btn_s_refresh = QPushButton("Refresh")
        self.btn_s_add = QPushButton("Add Staff")
        self.btn_s_edit = QPushButton("Edit Selected")
        self.btn_s_toggle = QPushButton("Toggle Active")
        self.btn_s_delete = QPushButton("Delete (Hard)")

        self.btn_s_refresh.clicked.connect(self.refresh_staff)
        self.btn_s_add.clicked.connect(self.add_staff)
        self.btn_s_edit.clicked.connect(self.edit_staff)
        self.btn_s_toggle.clicked.connect(self.toggle_staff_active)
        self.btn_s_delete.clicked.connect(self.delete_staff_hard)

        for b in [self.btn_s_refresh, self.btn_s_add, self.btn_s_edit, self.btn_s_toggle, self.btn_s_delete]:
            btns.addWidget(b)
        btns.addStretch(1)
        btns.addWidget(QLabel("Not: Staff silmek FK (UserAccount/Reservation/...) yüzünden hata verebilir."))

        layout.addLayout(btns)

        self.tbl_staff = QTableWidget(0, 8)
        self.tbl_staff.setHorizontalHeaderLabels([
            "StaffId", "FirstName", "LastName", "Title", "DepartmentId", "Phone", "Email", "IsActive"
        ])
        self.tbl_staff.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl_staff.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl_staff.verticalHeader().setVisible(False)

        layout.addWidget(self.tbl_staff)
        w.setLayout(layout)
        return w

    def refresh_staff(self):
        q = text("""
            SELECT StaffId, FirstName, LastName, Title, DepartmentId, Phone, Email, IsActive
            FROM Staff
            ORDER BY StaffId
        """)
        with engine.connect() as conn:
            rows = list(conn.execute(q).mappings().all())

        self.tbl_staff.setRowCount(0)
        for r in rows:
            row_idx = self.tbl_staff.rowCount()
            self.tbl_staff.insertRow(row_idx)

            def put(col, val, center=False):
                item = QTableWidgetItem("" if val is None else str(val))
                if center:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tbl_staff.setItem(row_idx, col, item)

            put(0, r["StaffId"], True)
            put(1, r["FirstName"])
            put(2, r["LastName"])
            put(3, r["Title"])
            put(4, r["DepartmentId"], True)
            put(5, r["Phone"])
            put(6, r["Email"])
            put(7, 1 if r["IsActive"] else 0, True)

        self.tbl_staff.resizeColumnsToContents()

    def _selected_staff(self):
        items = self.tbl_staff.selectedItems()
        if not items:
            return None
        row = items[0].row()

        def get(col):
            it = self.tbl_staff.item(row, col)
            return it.text() if it else ""

        return {
            "StaffId": int(get(0)),
            "FirstName": get(1),
            "LastName": get(2),
            "Title": get(3),
            "DepartmentId": int(get(4)) if get(4).strip() else None,
            "Phone": get(5),
            "Email": get(6),
            "IsActive": self._to_int_bool(get(7)),
        }

    def add_staff(self):
        departments = self.load_departments()
        dlg = StaffDialog(departments=departments, initial=None, parent=self)
        if dlg.exec() != dlg.DialogCode.Accepted:
            return
        data = dlg.get_data()

        q = text("""
            INSERT INTO Staff (FirstName, LastName, Title, DepartmentId, Phone, Email, IsActive)
            VALUES (:fn, :ln, :t, :did, :ph, :em, :act)
        """)
        try:
            with engine.begin() as conn:
                conn.execute(q, {
                    "fn": data["FirstName"],
                    "ln": data["LastName"],
                    "t": data["Title"],
                    "did": data["DepartmentId"],
                    "ph": data["Phone"],
                    "em": data["Email"],
                    "act": data["IsActive"],
                })
        except Exception as e:
            QMessageBox.critical(self, "DB Error", f"Insert failed:\n{e}")
            return

        self.refresh_staff()

    def edit_staff(self):
        selected = self._selected_staff()
        if not selected:
            QMessageBox.information(self, "Info", "Select a staff row first.")
            return

        departments = self.load_departments()
        dlg = StaffDialog(departments=departments, initial=selected, parent=self)
        if dlg.exec() != dlg.DialogCode.Accepted:
            return
        data = dlg.get_data()

        q = text("""
            UPDATE Staff
            SET FirstName=:fn, LastName=:ln, Title=:t, DepartmentId=:did, Phone=:ph, Email=:em, IsActive=:act
            WHERE StaffId=:id
        """)
        try:
            with engine.begin() as conn:
                conn.execute(q, {
                    "id": selected["StaffId"],
                    "fn": data["FirstName"],
                    "ln": data["LastName"],
                    "t": data["Title"],
                    "did": data["DepartmentId"],
                    "ph": data["Phone"],
                    "em": data["Email"],
                    "act": data["IsActive"],
                })
        except Exception as e:
            QMessageBox.critical(self, "DB Error", f"Update failed:\n{e}")
            return

        self.refresh_staff()

    def toggle_staff_active(self):
        selected = self._selected_staff()
        if not selected:
            QMessageBox.information(self, "Info", "Select a staff row first.")
            return

        new_val = 0 if selected["IsActive"] == 1 else 1
        q = text("UPDATE Staff SET IsActive=:a WHERE StaffId=:id")

        try:
            with engine.begin() as conn:
                conn.execute(q, {"a": new_val, "id": selected["StaffId"]})
        except Exception as e:
            QMessageBox.critical(self, "DB Error", f"Toggle failed:\n{e}")
            return

        self.refresh_staff()

    def delete_staff_hard(self):
        selected = self._selected_staff()
        if not selected:
            QMessageBox.information(self, "Info", "Select a staff row first.")
            return

        ok = QMessageBox.question(
            self, "Confirm Delete",
            f"Hard delete StaffId={selected['StaffId']} ?\nUserAccount/Reservation/ServiceRecord FK varsa hata verebilir.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if ok != QMessageBox.StandardButton.Yes:
            return

        q = text("DELETE FROM Staff WHERE StaffId=:id")
        try:
            with engine.begin() as conn:
                conn.execute(q, {"id": selected["StaffId"]})
        except Exception as e:
            QMessageBox.critical(self, "DB Error", f"Delete failed:\n{e}")
            return

        self.refresh_staff()

    # ================= PAYMENT TAB =================

    def _build_payments_tab(self):
        w = QWidget()
        layout = QVBoxLayout()

        btns = QHBoxLayout()
        self.btn_pay_refresh = QPushButton("Refresh")
        self.btn_pay_add = QPushButton("Add Payment")
        self.btn_pay_delete = QPushButton("Delete (Hard)")

        self.btn_pay_refresh.clicked.connect(self.refresh_payments)
        self.btn_pay_add.clicked.connect(self.add_payment)
        self.btn_pay_delete.clicked.connect(self.delete_payment_hard)

        btns.addWidget(self.btn_pay_refresh)
        btns.addWidget(self.btn_pay_add)
        btns.addWidget(self.btn_pay_delete)
        btns.addStretch(1)
        layout.addLayout(btns)

        self.tbl_pay = QTableWidget(0, 6)
        self.tbl_pay.setHorizontalHeaderLabels([
            "PaymentId", "ServiceRecordId", "PaymentDate", "Amount", "PaymentType", "Payer"
        ])
        self.tbl_pay.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl_pay.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl_pay.verticalHeader().setVisible(False)

        layout.addWidget(self.tbl_pay)
        w.setLayout(layout)
        return w

    # ================= DEFINITIONS TAB =================

    def _build_definitions_tab(self):
        from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget

        w = QWidget()
        layout = QVBoxLayout()
        tabs = QTabWidget()

        # Department (needs HospitalId FK)
        dept_fields = [
            FieldSpec("DepartmentName", "DepartmentName", "text", True),
            FieldSpec("Description", "Description", "text", False),
            FieldSpec("HospitalId", "Hospital", "fk", True, fk_loader=self.load_hospitals),
        ]
        tabs.addTab(
            GenericCrudWidget(
                table_name="Department",
                pk_name="DepartmentId",
                select_columns=["DepartmentId", "DepartmentName", "Description", "HospitalId"],
                fields=dept_fields,
                title="Department"
            ),
            "Department"
        )

        # RoomType
        roomtype_fields = [
            FieldSpec("TypeName", "TypeName", "text", True),
            FieldSpec("Description", "Description", "text", False),
            FieldSpec("DefaultCapacity", "DefaultCapacity", "int", True),
            FieldSpec("BaseDailyPrice", "BaseDailyPrice", "decimal", True),
        ]
        tabs.addTab(
            GenericCrudWidget(
                "RoomType", "RoomTypeId",
                ["RoomTypeId", "TypeName", "Description", "DefaultCapacity", "BaseDailyPrice"],
                roomtype_fields,
                "RoomType"
            ),
            "RoomType"
        )

        # ServiceCategory
        cat_fields = [
            FieldSpec("CategoryName", "CategoryName", "text", True),
            FieldSpec("Description", "Description", "text", False),
        ]
        tabs.addTab(
            GenericCrudWidget(
                "ServiceCategory", "ServiceCategoryId",
                ["ServiceCategoryId", "CategoryName", "Description"],
                cat_fields,
                "ServiceCategory"
            ),
            "ServiceCategory"
        )

        # HealthService (needs ServiceCategoryId FK)
        hs_fields = [
            FieldSpec("ServiceName", "ServiceName", "text", True),
            FieldSpec("ServiceCategoryId", "ServiceCategory", "fk", True, fk_loader=self.load_service_categories_fk),
            FieldSpec("BasePrice", "BasePrice", "decimal", True),
        ]
        tabs.addTab(
            GenericCrudWidget(
                "HealthService", "ServiceId",
                ["ServiceId", "ServiceName", "ServiceCategoryId", "BasePrice"],
                hs_fields,
                "HealthService"
            ),
            "HealthService"
        )

        # StateProgram
        sp_fields = [
            FieldSpec("ProgramName", "ProgramName", "text", True),
            FieldSpec("Description", "Description", "text", False),
            FieldSpec("CoverageRate", "CoverageRate (0.80 = %80)", "decimal", True),
        ]
        tabs.addTab(
            GenericCrudWidget(
                "StateProgram", "ProgramId",
                ["ProgramId", "ProgramName", "Description", "CoverageRate"],
                sp_fields,
                "StateProgram"
            ),
            "StateProgram"
        )

        # PaymentType
        pt_fields = [
            FieldSpec("PaymentTypeName", "PaymentTypeName", "text", True),
            FieldSpec("Description", "Description", "text", False),
        ]
        tabs.addTab(
            GenericCrudWidget(
                "PaymentType", "PaymentTypeId",
                ["PaymentTypeId", "PaymentTypeName", "Description"],
                pt_fields,
                "PaymentType"
            ),
            "PaymentType"
        )

        layout.addWidget(tabs)
        w.setLayout(layout)
        return w
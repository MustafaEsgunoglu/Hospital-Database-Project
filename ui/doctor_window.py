from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QMessageBox
)
from PyQt6.QtCore import Qt
from sqlalchemy import text
from db import get_engine

from ui.servicerecord_dialog import ServiceRecordDialog

engine = get_engine()

class DoctorWindow(QMainWindow):
    def __init__(self, session, on_logout):
        super().__init__()
        self.session = session
        self.on_logout = on_logout
        self.staff_id = session["staff_id"]
        self.setWindowTitle("Doctor Panel - Service Records")
        self.resize(1100, 580)

        root = QWidget()
        layout = QVBoxLayout()

        top = QHBoxLayout()
        top.addWidget(QLabel(f"DOCTOR | StaffId={self.staff_id}"))
        top.addStretch(1)
        btn_logout = QPushButton("Logout (Back to Login)")
        btn_logout.clicked.connect(self._logout)
        top.addWidget(btn_logout)
        layout.addLayout(top)

        btns = QHBoxLayout()
        self.btn_refresh = QPushButton("Refresh")
        self.btn_add = QPushButton("Add ServiceRecord")
        self.btn_edit = QPushButton("Edit Selected")
        self.btn_delete = QPushButton("Delete (Hard)")

        self.btn_refresh.clicked.connect(self.refresh)
        self.btn_add.clicked.connect(self.add_record)
        self.btn_edit.clicked.connect(self.edit_record)
        self.btn_delete.clicked.connect(self.delete_record_hard)

        for b in [self.btn_refresh, self.btn_add, self.btn_edit, self.btn_delete]:
            btns.addWidget(b)
        btns.addStretch(1)
        layout.addLayout(btns)

        self.tbl = QTableWidget(0, 10)
        self.tbl.setHorizontalHeaderLabels([
            "ServiceRecordId", "PatientId", "Patient", "ServiceId", "Service",
            "ProgramId", "Program", "ServiceDate", "TotalPrice", "PatientPayable"
        ])
        self.tbl.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl.verticalHeader().setVisible(False)
        layout.addWidget(self.tbl)

        root.setLayout(layout)
        self.setCentralWidget(root)

        self.refresh()

    def _logout(self):
        self.close()
        self.on_logout()

    # ---- data loaders for dialog ----
    def _load_patients(self):
        q = text("""
            SELECT PatientId, (FirstName + ' ' + LastName) AS FullName
            FROM Patient
            WHERE IsActive = 1 OR IsActive IS NULL
            ORDER BY PatientId
        """)
        with engine.connect() as conn:
            return list(conn.execute(q).mappings().all())

    def _load_services(self):
        q = text("""
            SELECT ServiceId, ServiceName, BasePrice
            FROM HealthService
            ORDER BY ServiceId
        """)
        with engine.connect() as conn:
            return list(conn.execute(q).mappings().all())

    def _load_programs(self):
        q = text("""
            SELECT ProgramId, ProgramName, CoverageRate
            FROM StateProgram
            ORDER BY ProgramId
        """)
        with engine.connect() as conn:
            return list(conn.execute(q).mappings().all())

    # ---- table refresh ----
    def refresh(self):
        q = text("""
            SELECT sr.ServiceRecordId,
                   sr.PatientId,
                   (p.FirstName + ' ' + p.LastName) AS PatientName,
                   sr.ServiceId,
                   hs.ServiceName,
                   sr.ProgramId,
                   sp.ProgramName,
                   CAST(sr.ServiceDate AS date) AS ServiceDate,
                   sr.TotalPrice,
                   sr.PatientPayableAmount
            FROM ServiceRecord sr
            JOIN Patient p ON p.PatientId = sr.PatientId
            JOIN HealthService hs ON hs.ServiceId = sr.ServiceId
            JOIN StateProgram sp ON sp.ProgramId = sr.ProgramId
            WHERE sr.DoctorId = :doc
            ORDER BY sr.ServiceRecordId DESC
        """)
        with engine.connect() as conn:
            rows = list(conn.execute(q, {"doc": self.staff_id}).mappings().all())

        self.tbl.setRowCount(0)
        for r in rows:
            i = self.tbl.rowCount()
            self.tbl.insertRow(i)
            self._put(i, 0, r["ServiceRecordId"], True)
            self._put(i, 1, r["PatientId"], True)
            self._put(i, 2, r["PatientName"])
            self._put(i, 3, r["ServiceId"], True)
            self._put(i, 4, r["ServiceName"])
            self._put(i, 5, r["ProgramId"], True)
            self._put(i, 6, r["ProgramName"])
            self._put(i, 7, str(r["ServiceDate"]))
            self._put(i, 8, r["TotalPrice"], True)
            self._put(i, 9, r["PatientPayableAmount"], True)

        self.tbl.resizeColumnsToContents()

    def _put(self, row, col, val, center=False):
        item = QTableWidgetItem("" if val is None else str(val))
        if center:
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tbl.setItem(row, col, item)

    def _selected(self):
        items = self.tbl.selectedItems()
        if not items:
            return None
        row = items[0].row()

        def get(c):
            it = self.tbl.item(row, c)
            return it.text() if it else ""

        return {
            "ServiceRecordId": int(get(0)),
            "PatientId": int(get(1)),
            "ServiceId": int(get(3)),
            "ProgramId": int(get(5)),
            "TotalPrice": float(get(8)) if get(8).strip() else 0.0,
        }

    # ---- CRUD ----
    def add_record(self):
        patients = self._load_patients()
        services = self._load_services()
        programs = self._load_programs()
        
        if not services:
            QMessageBox.warning(self, "Info", "No services found. Admin must add HealthService records first.")
            return

        if not programs:
            QMessageBox.warning(self, "Info", "No state programs found. Admin must add StateProgram records first.")
            return

        if not patients:
            QMessageBox.warning(self, "Info", "No patients found. Receptionist must add patients first.")
            return

        dlg = ServiceRecordDialog(patients=patients, services=services, programs=programs, parent=self)
        if dlg.exec() != dlg.DialogCode.Accepted:
            return
        data = dlg.get_data()

        q = text("""
            INSERT INTO ServiceRecord
            (PatientId, ServiceId, DoctorId, ProgramId, ServiceDate, TotalPrice, StateCoveredAmount, PatientPayableAmount)
            VALUES (:pid, :sid, :doc, :prg, :dt, :tot, :cov, :pay)
        """)
        try:
            with engine.begin() as conn:
                conn.execute(q, {
                    "pid": data["PatientId"],
                    "sid": data["ServiceId"],
                    "doc": self.staff_id,
                    "prg": data["ProgramId"],
                    "dt": data["ServiceDate"],
                    "tot": data["TotalPrice"],
                    "cov": data["StateCoveredAmount"],
                    "pay": data["PatientPayableAmount"],
                })
        except Exception as e:
            QMessageBox.critical(self, "DB Error", f"Insert failed:\n{e}")
            return

        self.refresh()

    def edit_record(self):
        selected = self._selected()
        if not selected:
            QMessageBox.information(self, "Info", "Select a service record first.")
            return

        patients = self._load_patients()
        services = self._load_services()
        programs = self._load_programs()

        dlg = ServiceRecordDialog(patients=patients, services=services, programs=programs, initial=selected, parent=self)
        if dlg.exec() != dlg.DialogCode.Accepted:
            return
        data = dlg.get_data()

        # Güvenlik: doktor sadece kendi kaydını güncellesin
        q = text("""
            UPDATE ServiceRecord
            SET PatientId=:pid, ServiceId=:sid, ProgramId=:prg, ServiceDate=:dt,
                TotalPrice=:tot, StateCoveredAmount=:cov, PatientPayableAmount=:pay
            WHERE ServiceRecordId=:id AND DoctorId=:doc
        """)
        try:
            with engine.begin() as conn:
                conn.execute(q, {
                    "id": selected["ServiceRecordId"],
                    "doc": self.staff_id,
                    "pid": data["PatientId"],
                    "sid": data["ServiceId"],
                    "prg": data["ProgramId"],
                    "dt": data["ServiceDate"],
                    "tot": data["TotalPrice"],
                    "cov": data["StateCoveredAmount"],
                    "pay": data["PatientPayableAmount"],
                })
        except Exception as e:
            QMessageBox.critical(self, "DB Error", f"Update failed:\n{e}")
            return

        self.refresh()

    def delete_record_hard(self):
        selected = self._selected()
        if not selected:
            QMessageBox.information(self, "Info", "Select a service record first.")
            return

        ok = QMessageBox.question(
            self, "Confirm Delete",
            f"Hard delete ServiceRecordId={selected['ServiceRecordId']}?\nPayment FK varsa hata verebilir.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if ok != QMessageBox.StandardButton.Yes:
            return

        q = text("DELETE FROM ServiceRecord WHERE ServiceRecordId=:id AND DoctorId=:doc")
        try:
            with engine.begin() as conn:
                conn.execute(q, {"id": selected["ServiceRecordId"], "doc": self.staff_id})
        except Exception as e:
            QMessageBox.critical(self, "DB Error", f"Delete failed:\n{e}")
            return

        self.refresh()

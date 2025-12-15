from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QTabWidget, QTableWidget, QTableWidgetItem, QMessageBox
)
from PyQt6.QtCore import Qt
from sqlalchemy import text
from db import get_engine

from ui.patient_dialog import PatientDialog
from ui.reservation_dialog import ReservationDialog

engine = get_engine()

class ReceptionistWindow(QMainWindow):
    def __init__(self, session, on_logout):
        super().__init__()
        self.session = session
        self.on_logout = on_logout
        self.setWindowTitle("Receptionist Panel")
        self.resize(1050, 600)

        root = QWidget()
        layout = QVBoxLayout()

        top = QHBoxLayout()
        top.addWidget(QLabel(f"RECEPTIONIST | StaffId={session['staff_id']}"))
        top.addStretch(1)
        btn_logout = QPushButton("Logout (Back to Login)")
        btn_logout.clicked.connect(self._logout)
        top.addWidget(btn_logout)
        layout.addLayout(top)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_patients_tab(), "Patients")
        self.tabs.addTab(self._build_reservations_tab(), "Reservations")
        self.tabs.addTab(self._build_availability_tab(), "Room Availability")
        layout.addWidget(self.tabs)

        root.setLayout(layout)
        self.setCentralWidget(root)

        self.refresh_patients()
        self.refresh_reservations()
        self.refresh_availability()

    def _logout(self):
        self.close()
        self.on_logout()

    # ---------------- PATIENTS TAB ----------------
    def _build_patients_tab(self):
        w = QWidget()
        layout = QVBoxLayout()

        btns = QHBoxLayout()
        self.btn_p_refresh = QPushButton("Refresh")
        self.btn_p_add = QPushButton("Add Patient")
        self.btn_p_edit = QPushButton("Edit Selected")
        self.btn_p_toggle = QPushButton("Toggle Active")
        self.btn_p_delete = QPushButton("Delete (Hard)")

        self.btn_p_refresh.clicked.connect(self.refresh_patients)
        self.btn_p_add.clicked.connect(self.add_patient)
        self.btn_p_edit.clicked.connect(self.edit_patient)
        self.btn_p_toggle.clicked.connect(self.toggle_patient_active)
        self.btn_p_delete.clicked.connect(self.delete_patient_hard)

        for b in [self.btn_p_refresh, self.btn_p_add, self.btn_p_edit, self.btn_p_toggle, self.btn_p_delete]:
            btns.addWidget(b)
        btns.addStretch(1)
        layout.addLayout(btns)

        self.tbl_patients = QTableWidget(0, 6)
        self.tbl_patients.setHorizontalHeaderLabels(["PatientId", "FirstName", "LastName", "Phone", "Email", "IsActive"])
        self.tbl_patients.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl_patients.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl_patients.verticalHeader().setVisible(False)

        layout.addWidget(self.tbl_patients)
        w.setLayout(layout)
        return w

    def refresh_patients(self):
        q = text("""
            SELECT PatientId, FirstName, LastName, TCNo, BirthDate, Gender, Phone, Email, Address, IsActive
            FROM Patient
            ORDER BY PatientId
        """)
        with engine.connect() as conn:
            rows = list(conn.execute(q).mappings().all())

        self.tbl_patients.setRowCount(0)
        for r in rows:
            i = self.tbl_patients.rowCount()
            self.tbl_patients.insertRow(i)
            self._put(self.tbl_patients, i, 0, r["PatientId"], True)
            self._put(self.tbl_patients, i, 1, r["FirstName"])
            self._put(self.tbl_patients, i, 2, r["LastName"])
            self._put(self.tbl_patients, i, 3, r.get("Phone"))
            self._put(self.tbl_patients, i, 4, r.get("Email"))
            self._put(self.tbl_patients, i, 5, 1 if r["IsActive"] else 0, True)

        self.tbl_patients.resizeColumnsToContents()

    def _selected_patient(self):
        items = self.tbl_patients.selectedItems()
        if not items:
            return None
        row = items[0].row()
        def get(c): 
            it = self.tbl_patients.item(row, c)
            return it.text() if it else ""
        return {
            "PatientId": int(get(0)),
            "FirstName": get(1),
            "LastName": get(2),
            "Phone": get(3),
            "Email": get(4),
            "IsActive": (get(5).strip().lower() in ("1", "true", "yes")),
        }

    def add_patient(self):
        dlg = PatientDialog(parent=self)
        if dlg.exec() != dlg.DialogCode.Accepted:
            return
        data = dlg.get_data()

        q = text("""
            INSERT INTO Patient
            (FirstName, LastName, TCNo, BirthDate, Gender, Phone, Email, Address, IsActive)
            VALUES (:fn, :ln, :tc, :bd, :g, :ph, :em, :ad, :act)
        """)
        try:
            with engine.begin() as conn:
                conn.execute(q, {
                    "fn": data["FirstName"],
                    "ln": data["LastName"],
                    "tc": data["TCNo"],
                    "bd": data["BirthDate"],
                    "g": data["Gender"],
                    "ph": data["Phone"],
                    "em": data["Email"],
                    "ad": data["Address"],
                    "act": data["IsActive"],
                })
        except Exception as e:
            QMessageBox.critical(self, "DB Error", f"Insert failed:\n{e}")
            return

        self.refresh_patients()


    def edit_patient(self):
        selected = self._selected_patient()
        if not selected:
            QMessageBox.information(self, "Info", "Select a patient first.")
            return

        dlg = PatientDialog(initial=selected, parent=self)
        if dlg.exec() != dlg.DialogCode.Accepted:
            return
        data = dlg.get_data()

        q = text("""
            UPDATE Patient
            SET FirstName=:fn, LastName=:ln, Phone=:ph, Email=:em, IsActive=:act
            WHERE PatientId=:id
        """)
        try:
            with engine.begin() as conn:
                conn.execute(q, {
                    "id": selected["PatientId"],
                    "fn": data["FirstName"], "ln": data["LastName"],
                    "ph": data["Phone"], "em": data["Email"],
                    "act": data["IsActive"]
                })
        except Exception as e:
            QMessageBox.critical(self, "DB Error", f"Update failed:\n{e}")
            return

        self.refresh_patients()

    def toggle_patient_active(self):
        selected = self._selected_patient()
        if not selected:
            QMessageBox.information(self, "Info", "Select a patient first.")
            return

        new_val = 0 if selected["IsActive"] else 1
        q = text("UPDATE Patient SET IsActive=:a WHERE PatientId=:id")
        try:
            with engine.begin() as conn:
                conn.execute(q, {"a": new_val, "id": selected["PatientId"]})
        except Exception as e:
            QMessageBox.critical(self, "DB Error", f"Toggle failed:\n{e}")
            return
        self.refresh_patients()

    def delete_patient_hard(self):
        selected = self._selected_patient()
        if not selected:
            QMessageBox.information(self, "Info", "Select a patient first.")
            return
        ok = QMessageBox.question(
            self, "Confirm Delete",
            f"Hard delete PatientId={selected['PatientId']}?\nFK varsa hata verebilir.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if ok != QMessageBox.StandardButton.Yes:
            return
        q = text("DELETE FROM Patient WHERE PatientId=:id")
        try:
            with engine.begin() as conn:
                conn.execute(q, {"id": selected["PatientId"]})
        except Exception as e:
            QMessageBox.critical(self, "DB Error", f"Delete failed:\n{e}")
            return
        self.refresh_patients()

    # ---------------- RESERVATIONS TAB ----------------
    def _build_reservations_tab(self):
        w = QWidget()
        layout = QVBoxLayout()

        btns = QHBoxLayout()
        self.btn_r_refresh = QPushButton("Refresh")
        self.btn_r_add = QPushButton("Add Reservation")
        self.btn_r_edit = QPushButton("Edit Selected")
        self.btn_r_cancel = QPushButton("Cancel Selected")
        self.btn_r_delete = QPushButton("Delete (Hard)")

        self.btn_r_refresh.clicked.connect(self.refresh_reservations)
        self.btn_r_add.clicked.connect(self.add_reservation)
        self.btn_r_edit.clicked.connect(self.edit_reservation)
        self.btn_r_cancel.clicked.connect(self.cancel_reservation)
        self.btn_r_delete.clicked.connect(self.delete_reservation_hard)

        for b in [self.btn_r_refresh, self.btn_r_add, self.btn_r_edit, self.btn_r_cancel, self.btn_r_delete]:
            btns.addWidget(b)
        btns.addStretch(1)
        layout.addLayout(btns)

        self.tbl_res = QTableWidget(0, 8)
        self.tbl_res.setHorizontalHeaderLabels([
            "ReservationId", "PatientId", "Patient", "RoomId", "StartDate", "EndDate", "StatusId", "Status"
        ])
        self.tbl_res.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl_res.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl_res.verticalHeader().setVisible(False)

        layout.addWidget(self.tbl_res)
        w.setLayout(layout)
        return w

    def _load_statuses(self):
        # ReservationStatus tablon farklı isimliyse burada düzeltiriz.
        q = text("SELECT StatusId, StatusName FROM ReservationStatus ORDER BY StatusId")
        with engine.connect() as conn:
            return list(conn.execute(q).mappings().all())

    def _load_patients_for_combo(self):
        q = text("""
            SELECT PatientId, (FirstName + ' ' + LastName) AS FullName
            FROM Patient
            WHERE IsActive = 1 OR IsActive IS NULL
            ORDER BY PatientId
        """)
        with engine.connect() as conn:
            return list(conn.execute(q).mappings().all())

    def _load_rooms_for_combo(self):
        q = text("""
            SELECT r.RoomId,
                   ('RoomId=' + CAST(r.RoomId AS varchar(20))) AS Display
            FROM Room r
            WHERE r.IsActive = 1 OR r.IsActive IS NULL
            ORDER BY r.RoomId
        """)
        with engine.connect() as conn:
            return list(conn.execute(q).mappings().all())

    def refresh_reservations(self):
        q = text("""
            SELECT res.ReservationId,
                   res.PatientId,
                   (p.FirstName + ' ' + p.LastName) AS PatientName,
                   res.RoomId,
                   CAST(res.StartDate AS date) AS StartDate,
                   CAST(res.EndDate AS date) AS EndDate,
                   res.StatusId,
                   st.StatusName
            FROM Reservation res
            JOIN Patient p ON p.PatientId = res.PatientId
            JOIN ReservationStatus st ON st.StatusId = res.StatusId
            ORDER BY res.ReservationId DESC
        """)
        with engine.connect() as conn:
            rows = list(conn.execute(q).mappings().all())

        self.tbl_res.setRowCount(0)
        for r in rows:
            i = self.tbl_res.rowCount()
            self.tbl_res.insertRow(i)
            self._put(self.tbl_res, i, 0, r["ReservationId"], True)
            self._put(self.tbl_res, i, 1, r["PatientId"], True)
            self._put(self.tbl_res, i, 2, r["PatientName"])
            self._put(self.tbl_res, i, 3, r["RoomId"], True)
            self._put(self.tbl_res, i, 4, str(r["StartDate"]))
            self._put(self.tbl_res, i, 5, str(r["EndDate"]))
            self._put(self.tbl_res, i, 6, r["StatusId"], True)
            self._put(self.tbl_res, i, 7, r["StatusName"])

        self.tbl_res.resizeColumnsToContents()

    def _selected_reservation(self):
        items = self.tbl_res.selectedItems()
        if not items:
            return None
        row = items[0].row()
        def get(c):
            it = self.tbl_res.item(row, c)
            return it.text() if it else ""
        return {
            "ReservationId": int(get(0)),
            "PatientId": int(get(1)),
            "RoomId": int(get(3)),
            "StatusId": int(get(6)),
        }

    def add_reservation(self):
        patients = self._load_patients_for_combo()
        rooms = self._load_rooms_for_combo()
        statuses = self._load_statuses()

        dlg = ReservationDialog(patients=patients, rooms=rooms, statuses=statuses, parent=self)
        if dlg.exec() != dlg.DialogCode.Accepted:
            return
        data = dlg.get_data()

        # Çakışma kontrolü (aynı oda, tarih aralığı overlap)
        overlap_q = text("""
            SELECT COUNT(1)
            FROM Reservation
            WHERE RoomId = :room
              AND StatusId <> :cancel
              AND NOT (EndDate <= :start OR StartDate >= :end)
        """)
        # Cancel status id bilinmiyorsa 0 verip devre dışı kalır; idealde "Cancelled" id’sini buluruz.
        cancel_id = next((s["StatusId"] for s in statuses if str(s["StatusName"]).lower().startswith("cancel")), 0)

        with engine.connect() as conn:
            cnt = int(conn.execute(overlap_q, {
                "room": data["RoomId"],
                "cancel": cancel_id,
                "start": data["StartDate"],
                "end": data["EndDate"],
            }).scalar() or 0)

        if cnt > 0:
            QMessageBox.warning(self, "Not Available", "Selected room is not available for that date range.")
            return

        q = text("""
                INSERT INTO Reservation
                (PatientId, RoomId, CreatedByStaffId, StatusId, StartDate, EndDate, CreatedDate)
                VALUES (:pid, :rid, :cb, :sid, :sd, :ed, CAST(GETDATE() AS date))
            """)
        try:
            with engine.begin() as conn:
                conn.execute(q, {
                    "pid": data["PatientId"],
                    "rid": data["RoomId"],
                    "cb": self.session["staff_id"],
                    "sid": data["StatusId"],
                    "sd": data["StartDate"],
                    "ed": data["EndDate"],
                })
        except Exception as e:
            QMessageBox.critical(self, "DB Error", f"Insert failed:\n{e}")
            return

        self.refresh_reservations()
        self.refresh_availability()

    def edit_reservation(self):
        selected = self._selected_reservation()
        if not selected:
            QMessageBox.information(self, "Info", "Select a reservation first.")
            return

        patients = self._load_patients_for_combo()
        rooms = self._load_rooms_for_combo()
        statuses = self._load_statuses()

        dlg = ReservationDialog(patients=patients, rooms=rooms, statuses=statuses, initial=selected, parent=self)
        if dlg.exec() != dlg.DialogCode.Accepted:
            return
        data = dlg.get_data()

        q = text("""
            UPDATE Reservation
            SET PatientId=:pid, RoomId=:rid, StartDate=:sd, EndDate=:ed, StatusId=:sid
            WHERE ReservationId=:id
        """)
        try:
            with engine.begin() as conn:
                conn.execute(q, {
                    "id": selected["ReservationId"],
                    "pid": data["PatientId"],
                    "rid": data["RoomId"],
                    "sd": data["StartDate"],
                    "ed": data["EndDate"],
                    "sid": data["StatusId"],
                })
        except Exception as e:
            QMessageBox.critical(self, "DB Error", f"Update failed:\n{e}")
            return

        self.refresh_reservations()
        self.refresh_availability()

    def cancel_reservation(self):
        selected = self._selected_reservation()
        if not selected:
            QMessageBox.information(self, "Info", "Select a reservation first.")
            return

        statuses = self._load_statuses()
        cancel_id = next((s["StatusId"] for s in statuses if str(s["StatusName"]).lower().startswith("cancel")), None)
        if cancel_id is None:
            QMessageBox.warning(self, "Error", "No 'Cancelled' status found in ReservationStatus.")
            return

        q = text("UPDATE Reservation SET StatusId=:sid WHERE ReservationId=:id")
        try:
            with engine.begin() as conn:
                conn.execute(q, {"sid": cancel_id, "id": selected["ReservationId"]})
        except Exception as e:
            QMessageBox.critical(self, "DB Error", f"Cancel failed:\n{e}")
            return

        self.refresh_reservations()
        self.refresh_availability()

    def delete_reservation_hard(self):
        selected = self._selected_reservation()
        if not selected:
            QMessageBox.information(self, "Info", "Select a reservation first.")
            return
        ok = QMessageBox.question(
            self, "Confirm Delete",
            f"Hard delete ReservationId={selected['ReservationId']}?\nFK varsa hata verebilir.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if ok != QMessageBox.StandardButton.Yes:
            return

        q = text("DELETE FROM Reservation WHERE ReservationId=:id")
        try:
            with engine.begin() as conn:
                conn.execute(q, {"id": selected["ReservationId"]})
        except Exception as e:
            QMessageBox.critical(self, "DB Error", f"Delete failed:\n{e}")
            return

        self.refresh_reservations()
        self.refresh_availability()

    # ---------------- AVAILABILITY TAB ----------------
    def _build_availability_tab(self):
        w = QWidget()
        layout = QVBoxLayout()

        btns = QHBoxLayout()
        self.btn_a_refresh = QPushButton("Refresh Availability")
        self.btn_a_refresh.clicked.connect(self.refresh_availability)
        btns.addWidget(self.btn_a_refresh)
        btns.addStretch(1)
        layout.addLayout(btns)

        self.tbl_av = QTableWidget(0, 4)
        self.tbl_av.setHorizontalHeaderLabels(["RoomId", "TotalReservations", "ActiveReservations", "LastReservationEnd"])
        self.tbl_av.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl_av.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl_av.verticalHeader().setVisible(False)

        layout.addWidget(self.tbl_av)
        w.setLayout(layout)
        return w

    def refresh_availability(self):
        # Basit özet tablo (doluluk/rezerv sayısı)
        q = text("""
            SELECT r.RoomId,
                   COUNT(res.ReservationId) AS TotalReservations,
                   SUM(CASE WHEN st.StatusName NOT LIKE 'Cancel%' THEN 1 ELSE 0 END) AS ActiveReservations,
                   MAX(CAST(res.EndDate AS date)) AS LastReservationEnd
            FROM Room r
            LEFT JOIN Reservation res ON res.RoomId = r.RoomId
            LEFT JOIN ReservationStatus st ON st.StatusId = res.StatusId
            GROUP BY r.RoomId
            ORDER BY r.RoomId
        """)
        try:
            with engine.connect() as conn:
                rows = list(conn.execute(q).mappings().all())
        except Exception as e:
            # Şema farklıysa burada yakalarız.
            QMessageBox.critical(self, "DB Error", f"Availability query failed:\n{e}")
            return

        self.tbl_av.setRowCount(0)
        for r in rows:
            i = self.tbl_av.rowCount()
            self.tbl_av.insertRow(i)
            self._put(self.tbl_av, i, 0, r["RoomId"], True)
            self._put(self.tbl_av, i, 1, r["TotalReservations"] or 0, True)
            self._put(self.tbl_av, i, 2, r["ActiveReservations"] or 0, True)
            self._put(self.tbl_av, i, 3, "" if r["LastReservationEnd"] is None else str(r["LastReservationEnd"]))

        self.tbl_av.resizeColumnsToContents()

    # ---------------- tiny util ----------------
    def _put(self, table, row, col, val, center=False):
        item = QTableWidgetItem("" if val is None else str(val))
        if center:
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        table.setItem(row, col, item)

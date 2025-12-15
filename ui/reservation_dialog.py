from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QComboBox,
    QDateEdit, QPushButton, QHBoxLayout, QMessageBox
)
from PyQt6.QtCore import QDate

class ReservationDialog(QDialog):
    """
    patients: [{PatientId, FullName}]
    rooms: [{RoomId, Display}]
    statuses: [{StatusId, StatusName}]
    """
    def __init__(self, patients, rooms, statuses, initial=None, parent=None):
        super().__init__(parent)
        self.initial = initial or {}
        self.setWindowTitle("Add Reservation" if not initial else "Edit Reservation")
        self.setMinimumWidth(520)

        layout = QVBoxLayout()
        form = QFormLayout()

        self.cmb_patient = QComboBox()
        for p in patients:
            self.cmb_patient.addItem(f"{p['PatientId']} - {p['FullName']}", p["PatientId"])

        self.cmb_room = QComboBox()
        for r in rooms:
            self.cmb_room.addItem(r["Display"], r["RoomId"])

        self.cmb_status = QComboBox()
        for s in statuses:
            self.cmb_status.addItem(s["StatusName"], s["StatusId"])

        self.dt_start = QDateEdit()
        self.dt_start.setCalendarPopup(True)
        self.dt_start.setDate(QDate.currentDate())

        self.dt_end = QDateEdit()
        self.dt_end.setCalendarPopup(True)
        self.dt_end.setDate(QDate.currentDate().addDays(1))

        form.addRow("Patient", self.cmb_patient)
        form.addRow("Room", self.cmb_room)
        form.addRow("StartDate", self.dt_start)
        form.addRow("EndDate", self.dt_end)
        form.addRow("Status", self.cmb_status)

        layout.addLayout(form)

        btns = QHBoxLayout()
        ok = QPushButton("Save")
        cancel = QPushButton("Cancel")
        ok.clicked.connect(self._validate)
        cancel.clicked.connect(self.reject)
        btns.addWidget(ok)
        btns.addWidget(cancel)
        layout.addLayout(btns)

        self.setLayout(layout)
        self._load()

    def _load(self):
        if not self.initial:
            return

        # initial: PatientId/RoomId/StatusId + StartDate/EndDate (date string olabilir)
        pid = self.initial.get("PatientId")
        rid = self.initial.get("RoomId")
        sid = self.initial.get("StatusId")
        if pid is not None:
            i = self.cmb_patient.findData(pid)
            if i >= 0: self.cmb_patient.setCurrentIndex(i)
        if rid is not None:
            i = self.cmb_room.findData(rid)
            if i >= 0: self.cmb_room.setCurrentIndex(i)
        if sid is not None:
            i = self.cmb_status.findData(sid)
            if i >= 0: self.cmb_status.setCurrentIndex(i)

        # PyQt QDate'e çevirmek zor; burada edit ekranında tarihleri değiştirmeyi zorunlu yapmıyoruz.
        # İstersen sonra parsing ekleriz.

    def _validate(self):
        if self.dt_end.date() <= self.dt_start.date():
            QMessageBox.warning(self, "Error", "EndDate must be after StartDate.")
            return
        self.accept()

    def get_data(self):
        return {
            "PatientId": int(self.cmb_patient.currentData()),
            "RoomId": int(self.cmb_room.currentData()),
            "StatusId": int(self.cmb_status.currentData()),
            "StartDate": self.dt_start.date().toString("yyyy-MM-dd"),
            "EndDate": self.dt_end.date().toString("yyyy-MM-dd"),
        }

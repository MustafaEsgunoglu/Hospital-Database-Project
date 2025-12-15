from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDateEdit,
    QComboBox, QCheckBox, QPushButton, QHBoxLayout, QMessageBox
)
from PyQt6.QtCore import QDate

class PatientDialog(QDialog):
    def __init__(self, initial=None, parent=None):
        super().__init__(parent)
        self.initial = initial or {}
        self.setWindowTitle("Add Patient" if not initial else "Edit Patient")
        self.setMinimumWidth(450)

        layout = QVBoxLayout()
        form = QFormLayout()

        self.first = QLineEdit()
        self.last = QLineEdit()
        self.tcno = QLineEdit()
        self.phone = QLineEdit()
        self.email = QLineEdit()
        self.address = QLineEdit()

        self.birth = QDateEdit()
        self.birth.setCalendarPopup(True)
        self.birth.setDate(QDate(1990, 1, 1))

        self.gender = QComboBox()
        self.gender.addItems(["Male", "Female", "Other"])

        self.chk_active = QCheckBox("IsActive")

        form.addRow("FirstName", self.first)
        form.addRow("LastName", self.last)
        form.addRow("TCNo", self.tcno)
        form.addRow("BirthDate", self.birth)
        form.addRow("Gender", self.gender)
        form.addRow("Phone", self.phone)
        form.addRow("Email", self.email)
        form.addRow("Address", self.address)
        form.addRow("", self.chk_active)

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
            self.chk_active.setChecked(True)
            return

        self.first.setText(self.initial.get("FirstName", ""))
        self.last.setText(self.initial.get("LastName", ""))
        self.tcno.setText(self.initial.get("TCNo", ""))
        self.phone.setText(self.initial.get("Phone", ""))
        self.email.setText(self.initial.get("Email", ""))
        self.address.setText(self.initial.get("Address", ""))

        # BirthDate: 'YYYY-MM-DD' veya 'YYYY-MM-DD ...' gibi gelebilir
        bd = self.initial.get("BirthDate")
        if bd:
            s = str(bd)[:10]  # sadece YYYY-MM-DD
            parts = s.split("-")
            if len(parts) == 3:
                try:
                    y, m, d = map(int, parts)
                    self.birth.setDate(QDate(y, m, d))
                except Exception:
                    pass

        # Gender
        g = self.initial.get("Gender")
        if g:
            idx = self.gender.findText(str(g))
            if idx >= 0:
                self.gender.setCurrentIndex(idx)

        self.chk_active.setChecked(bool(self.initial.get("IsActive", True)))


    def _validate(self):
        if not self.first.text().strip() or not self.last.text().strip():
            QMessageBox.warning(self, "Error", "FirstName and LastName required.")
            return
        if not self.tcno.text().strip():
            QMessageBox.warning(self, "Error", "TCNo is required.")
            return
        self.accept()

    def get_data(self):
        return {
            "FirstName": self.first.text().strip(),
            "LastName": self.last.text().strip(),
            "TCNo": self.tcno.text().strip(),
            "BirthDate": self.birth.date().toString("yyyy-MM-dd"),
            "Gender": self.gender.currentText(),
            "Phone": self.phone.text().strip(),
            "Email": self.email.text().strip(),
            "Address": self.address.text().strip(),
            "IsActive": 1 if self.chk_active.isChecked() else 0,
        }

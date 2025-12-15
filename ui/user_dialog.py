# ui/user_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QCheckBox, QPushButton, QHBoxLayout, QMessageBox
)

class UserDialog(QDialog):
    """
    mode: "add" | "edit"
    roles: list[{"RoleId": int, "RoleName": str}]
    staff_list: list[{"StaffId": int, "FullName": str, "Title": str}]
    patient_list: list[{"PatientId": int, "FullName": str}]
    initial: dict or None
    """
    def __init__(self, mode, roles, staff_list, patient_list, initial=None, parent=None):
        super().__init__(parent)
        self.mode = mode
        self.roles = roles
        self.staff_list = staff_list
        self.patient_list = patient_list
        self.initial = initial or {}

        self.setWindowTitle("Add User" if mode == "add" else "Edit User")
        self.setMinimumWidth(420)

        layout = QVBoxLayout()
        form = QFormLayout()

        self.txt_username = QLineEdit()
        self.txt_password = QLineEdit()
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)

        self.cmb_role = QComboBox()
        for r in roles:
            self.cmb_role.addItem(r["RoleName"], r["RoleId"])

        # Staff combobox (None option)
        self.cmb_staff = QComboBox()
        self.cmb_staff.addItem("None", None)
        for s in staff_list:
            label = f"{s['StaffId']} - {s['FullName']} ({s['Title']})"
            self.cmb_staff.addItem(label, s["StaffId"])

        # Patient combobox (None option)
        self.cmb_patient = QComboBox()
        self.cmb_patient.addItem("None", None)
        for p in patient_list:
            label = f"{p['PatientId']} - {p['FullName']}"
            self.cmb_patient.addItem(label, p["PatientId"])

        self.chk_active = QCheckBox("IsActive")

        form.addRow("Username", self.txt_username)
        form.addRow("Password", self.txt_password)  # edit modunda boş bırakılırsa değişmez
        form.addRow("Role", self.cmb_role)
        form.addRow("Staff", self.cmb_staff)
        form.addRow("Patient", self.cmb_patient)
        form.addRow("", self.chk_active)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        self.btn_ok = QPushButton("Save")
        self.btn_cancel = QPushButton("Cancel")
        self.btn_ok.clicked.connect(self._validate)
        self.btn_cancel.clicked.connect(self.reject)

        btn_row.addWidget(self.btn_ok)
        btn_row.addWidget(self.btn_cancel)
        layout.addLayout(btn_row)

        self.setLayout(layout)
        self._load_initial()

    def _load_initial(self):
        if self.mode == "add":
            self.chk_active.setChecked(True)
            return

        self.txt_username.setText(str(self.initial.get("Username", "")))

        role_id = self.initial.get("RoleId", None)
        if role_id is not None:
            idx = self.cmb_role.findData(role_id)
            if idx >= 0:
                self.cmb_role.setCurrentIndex(idx)

        staff_id = self.initial.get("StaffId", None)
        idx = self.cmb_staff.findData(staff_id)
        if idx >= 0:
            self.cmb_staff.setCurrentIndex(idx)

        patient_id = self.initial.get("PatientId", None)
        idx = self.cmb_patient.findData(patient_id)
        if idx >= 0:
            self.cmb_patient.setCurrentIndex(idx)

        self.chk_active.setChecked(bool(self.initial.get("IsActive", True)))

    def _validate(self):
        username = self.txt_username.text().strip()
        if not username:
            QMessageBox.warning(self, "Error", "Username is required.")
            return

        if self.mode == "add" and not self.txt_password.text():
            QMessageBox.warning(self, "Error", "Password is required for new user.")
            return

        staff_id = self.cmb_staff.currentData()
        patient_id = self.cmb_patient.currentData()

        if staff_id is not None and patient_id is not None:
            QMessageBox.warning(self, "Error", "Staff and Patient cannot both be selected.")
            return

        self.accept()

    def get_data(self) -> dict:
        return {
            "Username": self.txt_username.text().strip(),
            "Password": self.txt_password.text(),  # edit modunda boş olabilir
            "RoleId": int(self.cmb_role.currentData()),
            "StaffId": self.cmb_staff.currentData(),
            "PatientId": self.cmb_patient.currentData(),
            "IsActive": 1 if self.chk_active.isChecked() else 0,
        }

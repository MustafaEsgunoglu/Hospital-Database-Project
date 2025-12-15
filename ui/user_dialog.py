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

        # roleId -> roleName map
        self.role_map = {int(r["RoleId"]): str(r["RoleName"]) for r in roles if r.get("RoleId") is not None}

        self.setWindowTitle("Add User" if mode == "add" else "Edit User")
        self.setMinimumWidth(420)

        layout = QVBoxLayout()
        self.form = QFormLayout()

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

        self.form.addRow("Username", self.txt_username)
        self.form.addRow("Password", self.txt_password)  # edit modunda boş bırakılırsa değişmez
        self.form.addRow("Role", self.cmb_role)
        self.form.addRow("Staff", self.cmb_staff)
        self.form.addRow("Patient", self.cmb_patient)
        self.form.addRow("", self.chk_active)

        layout.addLayout(self.form)

        btn_row = QHBoxLayout()
        self.btn_ok = QPushButton("Save")
        self.btn_cancel = QPushButton("Cancel")
        self.btn_ok.clicked.connect(self._validate)
        self.btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(self.btn_ok)
        btn_row.addWidget(self.btn_cancel)
        layout.addLayout(btn_row)

        self.setLayout(layout)

        # role change -> apply rules
        self.cmb_role.currentIndexChanged.connect(self._apply_role_rules)

        self._load_initial()
        self._apply_role_rules()

    def _role_name(self) -> str:
        rid = self.cmb_role.currentData()
        if rid is None:
            return ""
        return self.role_map.get(int(rid), "")

    def _set_row_visible(self, widget, visible: bool):
        widget.setVisible(visible)
        lbl = self.form.labelForField(widget)
        if lbl:
            lbl.setVisible(visible)

    def _apply_role_rules(self):
        """
        - If role == 'Patient' -> Patient required, Staff disabled
        - Else -> Staff required, Patient disabled
        - If no Patient role in DB -> Patient row hidden completely
        """
        role_name = self._role_name().lower().strip()

        has_patient_role = any(str(r.get("RoleName", "")).lower() == "patient" for r in self.roles)

        if not has_patient_role:
            # Projede hasta login yok: tamamen gizle
            self._set_row_visible(self.cmb_patient, False)
            self.cmb_patient.setCurrentIndex(0)
            self.cmb_patient.setEnabled(False)
        else:
            # hasta rolü varsa görünür kalsın, role'a göre enable/disable
            self._set_row_visible(self.cmb_patient, True)

        if role_name == "patient":
            # Patient user
            self.cmb_patient.setEnabled(True)
            self.cmb_staff.setEnabled(False)
            self.cmb_staff.setCurrentIndex(0)
        else:
            # Staff user (Admin/Doctor/Receptionist)
            self.cmb_staff.setEnabled(True)
            self.cmb_patient.setEnabled(False)
            self.cmb_patient.setCurrentIndex(0)

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

        role_name = self._role_name().lower().strip()

        staff_id = self.cmb_staff.currentData()
        patient_id = self.cmb_patient.currentData()

        # Role-based required checks
        if role_name == "patient":
            if patient_id is None:
                QMessageBox.warning(self, "Error", "Patient must be selected for Patient role.")
                return
            # force staff none
            staff_id = None
        else:
            if staff_id is None:
                QMessageBox.warning(self, "Error", "Staff must be selected for staff roles.")
                return
            # force patient none
            patient_id = None

        self.accept()

    def get_data(self) -> dict:
        role_id = int(self.cmb_role.currentData())
        role_name = self.role_map.get(role_id, "").lower().strip()

        staff_id = self.cmb_staff.currentData()
        patient_id = self.cmb_patient.currentData()

        # Force correct linkage
        if role_name == "patient":
            staff_id = None
        else:
            patient_id = None

        return {
            "Username": self.txt_username.text().strip(),
            "Password": self.txt_password.text(),  # edit modunda boş olabilir
            "RoleId": role_id,
            "StaffId": staff_id,
            "PatientId": patient_id,
            "IsActive": 1 if self.chk_active.isChecked() else 0,
        }

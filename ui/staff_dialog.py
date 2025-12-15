from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QCheckBox, QPushButton, QHBoxLayout, QMessageBox
)

class StaffDialog(QDialog):
    """
    departments: list[{"DepartmentId": int, "DepartmentName": str}]
    initial: dict or None
    """
    def __init__(self, departments, initial=None, parent=None):
        super().__init__(parent)
        self.departments = departments
        self.initial = initial or {}

        self.setWindowTitle("Add Staff" if not initial else "Edit Staff")
        self.setMinimumWidth(420)

        layout = QVBoxLayout()
        form = QFormLayout()

        self.first = QLineEdit()
        self.last = QLineEdit()
        self.title = QLineEdit()
        self.phone = QLineEdit()
        self.email = QLineEdit()

        self.cmb_dept = QComboBox()
        for d in departments:
            self.cmb_dept.addItem(d["DepartmentName"], d["DepartmentId"])

        self.chk_active = QCheckBox("IsActive")

        form.addRow("FirstName", self.first)
        form.addRow("LastName", self.last)
        form.addRow("Title", self.title)
        form.addRow("Department", self.cmb_dept)
        form.addRow("Phone", self.phone)
        form.addRow("Email", self.email)
        form.addRow("", self.chk_active)

        layout.addLayout(form)

        btns = QHBoxLayout()
        btn_ok = QPushButton("Save")
        btn_cancel = QPushButton("Cancel")
        btn_ok.clicked.connect(self._validate)
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)

        layout.addLayout(btns)
        self.setLayout(layout)

        self._load_initial()

    def _load_initial(self):
        if not self.initial:
            self.chk_active.setChecked(True)
            return

        self.first.setText(str(self.initial.get("FirstName", "")))
        self.last.setText(str(self.initial.get("LastName", "")))
        self.title.setText(str(self.initial.get("Title", "")))
        self.phone.setText(str(self.initial.get("Phone", "")))
        self.email.setText(str(self.initial.get("Email", "")))
        self.chk_active.setChecked(bool(self.initial.get("IsActive", True)))

        dept_id = self.initial.get("DepartmentId")
        if dept_id is not None:
            idx = self.cmb_dept.findData(dept_id)
            if idx >= 0:
                self.cmb_dept.setCurrentIndex(idx)

    def _validate(self):
        if not self.first.text().strip() or not self.last.text().strip():
            QMessageBox.warning(self, "Error", "FirstName and LastName are required.")
            return
        self.accept()

    def get_data(self):
        return {
            "FirstName": self.first.text().strip(),
            "LastName": self.last.text().strip(),
            "Title": self.title.text().strip(),
            "DepartmentId": int(self.cmb_dept.currentData()),
            "Phone": self.phone.text().strip(),
            "Email": self.email.text().strip(),
            "IsActive": 1 if self.chk_active.isChecked() else 0,
        }

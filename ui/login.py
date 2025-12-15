# ui/login.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox
)
from auth import login

class LoginWindow(QWidget):
    def __init__(self, on_success):
        super().__init__()
        self.on_success = on_success
        self.setWindowTitle("Hospital System - Login")
        self.setFixedWidth(320)

        layout = QVBoxLayout()
        
        self.username = QLineEdit()
        self.username.setPlaceholderText("Username (örn: admin)")

        self.password = QLineEdit()
        self.password.setPlaceholderText("Password (örn: 1234)")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)

        self.btn = QPushButton("Login")
        self.btn.clicked.connect(self.handle_login)

        layout.addWidget(QLabel("Please login"))
        layout.addWidget(self.username)
        layout.addWidget(self.password)
        layout.addWidget(self.btn)
        self.setLayout(layout)

    def handle_login(self):
        u = self.username.text().strip()
        p = self.password.text()

        if not u or not p:
            QMessageBox.warning(self, "Error", "Username and password required.")
            return

        session = login(u, p)
        if not session:
            QMessageBox.warning(self, "Error", "Invalid credentials or inactive user.")
            return

        self.on_success(session)

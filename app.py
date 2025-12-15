import sys
from PyQt6.QtWidgets import QApplication, QMessageBox

from ui.login import LoginWindow
from ui.admin_window import AdminWindow
from ui.doctor_window import DoctorWindow
from ui.receptionist_window import ReceptionistWindow

def main():
    app = QApplication(sys.argv)
    windows = {"login": None, "main": None}

    def show_login():
        if windows.get("main"):
            windows["main"].close()
            windows["main"] = None
        windows["login"] = LoginWindow(on_success=open_by_role)
        windows["login"].show()

    def open_by_role(session):
        role = (session["role_name"] or "").lower()

        if role == "admin":
            windows["main"] = AdminWindow(session, on_logout=show_login)
        elif role == "doctor":
            windows["main"] = DoctorWindow(session, on_logout=show_login)
        elif role == "receptionist":
            windows["main"] = ReceptionistWindow(session, on_logout=show_login)
        else:
            QMessageBox.critical(None, "Error", f"Unknown role: {session['role_name']}")
            return

        windows["login"].close()
        windows["login"] = None
        windows["main"].show()

    show_login()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

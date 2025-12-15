from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QComboBox, QDateEdit,
    QDoubleSpinBox, QLineEdit, QPushButton, QHBoxLayout, QMessageBox
)
from PyQt6.QtCore import QDate

class PaymentDialog(QDialog):
    """
    servicerecords: [{ServiceRecordId, Display}]
    payment_types: [{PaymentTypeId, PaymentTypeName}]
    """
    def __init__(self, servicerecords, payment_types, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Payment")
        self.setMinimumWidth(520)

        layout = QVBoxLayout()
        form = QFormLayout()

        self.cmb_sr = QComboBox()
        for sr in servicerecords:
            self.cmb_sr.addItem(sr["Display"], sr["ServiceRecordId"])

        self.cmb_pt = QComboBox()
        for pt in payment_types:
            self.cmb_pt.addItem(pt["PaymentTypeName"], pt["PaymentTypeId"])

        self.dt = QDateEdit()
        self.dt.setCalendarPopup(True)
        self.dt.setDate(QDate.currentDate())

        self.amount = QDoubleSpinBox()
        self.amount.setRange(0, 10**9)
        self.amount.setDecimals(2)

        self.payer = QLineEdit()
        self.payer.setPlaceholderText("Patient / Relative / Insurance / etc.")

        form.addRow("ServiceRecord", self.cmb_sr)
        form.addRow("PaymentType", self.cmb_pt)
        form.addRow("PaymentDate", self.dt)
        form.addRow("Amount", self.amount)
        form.addRow("Payer", self.payer)

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

    def _validate(self):
        if self.amount.value() <= 0:
            QMessageBox.warning(self, "Error", "Amount must be > 0.")
            return
        if not self.payer.text().strip():
            QMessageBox.warning(self, "Error", "Payer is required.")
            return
        self.accept()

    def get_data(self):
        return {
            "ServiceRecordId": int(self.cmb_sr.currentData()),
            "PaymentTypeId": int(self.cmb_pt.currentData()),
            "PaymentDate": self.dt.date().toString("yyyy-MM-dd"),
            "Amount": float(self.amount.value()),
            "Payer": self.payer.text().strip(),
        }

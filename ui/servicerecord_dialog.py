from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QComboBox, QDateEdit,
    QDoubleSpinBox, QPushButton, QHBoxLayout, QMessageBox, QLabel
)
from PyQt6.QtCore import QDate

class ServiceRecordDialog(QDialog):
    """
    patients: [{PatientId, FullName}]
    services: [{ServiceId, ServiceName, BasePrice}]
    programs: [{ProgramId, ProgramName, CoverageRate}]
    initial: dict or None
    """
    def __init__(self, patients, services, programs, initial=None, parent=None):
        super().__init__(parent)
        self.initial = initial or {}
        self.services = services
        self.programs = programs

        self.setWindowTitle("Add ServiceRecord" if not initial else "Edit ServiceRecord")
        self.setMinimumWidth(520)

        layout = QVBoxLayout()
        form = QFormLayout()

        self.cmb_patient = QComboBox()
        for p in patients:
            self.cmb_patient.addItem(f"{p['PatientId']} - {p['FullName']}", p["PatientId"])

        self.cmb_service = QComboBox()
        for s in services:
            label = f"{s['ServiceId']} - {s['ServiceName']} (Base: {s['BasePrice']})"
            self.cmb_service.addItem(label, s["ServiceId"])

        self.cmb_program = QComboBox()
        for pr in programs:
            label = f"{pr['ProgramId']} - {pr['ProgramName']} (Rate: {pr['CoverageRate']})"
            self.cmb_program.addItem(label, pr["ProgramId"])

        self.dt = QDateEdit()
        self.dt.setCalendarPopup(True)
        self.dt.setDate(QDate.currentDate())

        self.total = QDoubleSpinBox()
        self.total.setRange(0, 10**9)
        self.total.setDecimals(2)

        self.covered = QDoubleSpinBox()
        self.covered.setRange(0, 10**9)
        self.covered.setDecimals(2)
        self.covered.setReadOnly(True)

        self.payable = QDoubleSpinBox()
        self.payable.setRange(0, 10**9)
        self.payable.setDecimals(2)
        self.payable.setReadOnly(True)

        self.lbl_hint = QLabel("Not: TotalPrice is editable. Covered/Payable auto-calculated from Program CoverageRate.")

        # signals
        self.cmb_service.currentIndexChanged.connect(self._sync_total_from_service)
        self.cmb_program.currentIndexChanged.connect(self._recalc)
        self.total.valueChanged.connect(self._recalc)

        form.addRow("Patient", self.cmb_patient)
        form.addRow("Service", self.cmb_service)
        form.addRow("Program", self.cmb_program)
        form.addRow("ServiceDate", self.dt)
        form.addRow("TotalPrice", self.total)
        form.addRow("StateCoveredAmount", self.covered)
        form.addRow("PatientPayableAmount", self.payable)

        layout.addLayout(form)
        layout.addWidget(self.lbl_hint)

        btns = QHBoxLayout()
        ok = QPushButton("Save")
        cancel = QPushButton("Cancel")
        ok.clicked.connect(self._validate)
        cancel.clicked.connect(self.reject)
        btns.addWidget(ok)
        btns.addWidget(cancel)
        layout.addLayout(btns)

        self.setLayout(layout)
        self._load_initial_or_defaults()

    def _find_service(self, service_id: int):
        for s in self.services:
            if int(s["ServiceId"]) == int(service_id):
                return s
        return None

    def _find_program(self, program_id: int):
        for p in self.programs:
            if int(p["ProgramId"]) == int(program_id):
                return p
        return None

    def _sync_total_from_service(self):
        if self.initial:
            return

        sid = self.cmb_service.currentData()
        if sid is None:
            # service list boşsa patlama
            self.total.setValue(0)
            self._recalc()
            return

        s = self._find_service(int(sid))
        if s is not None:
            try:
                self.total.blockSignals(True)
                self.total.setValue(float(s["BasePrice"] or 0))
            finally:
                self.total.blockSignals(False)

        self._recalc()


    def _recalc(self):
        pid = self.cmb_program.currentData()
        if pid is None:
            self.covered.setValue(0)
            self.payable.setValue(float(self.total.value()))
            return

        pr = self._find_program(int(pid))
        rate = float(pr["CoverageRate"] or 0) if pr else 0.0

        total = float(self.total.value())
        covered = total * rate
        payable = total - covered

        self.covered.setValue(round(covered, 2))
        self.payable.setValue(round(payable, 2))

    def _load_initial_or_defaults(self):
        if not self.initial:
            self._sync_total_from_service()
            self._recalc()
            return

        # initial select
        for (cmb, key) in [(self.cmb_patient, "PatientId"), (self.cmb_service, "ServiceId"), (self.cmb_program, "ProgramId")]:
            v = self.initial.get(key)
            if v is not None:
                idx = cmb.findData(int(v))
                if idx >= 0:
                    cmb.setCurrentIndex(idx)

        # total loaded
        try:
            self.total.setValue(float(self.initial.get("TotalPrice") or 0))
        except Exception:
            self.total.setValue(0)

        # date parsing: basitçe bugün bırakıyoruz; istersen sonra parse ederiz
        self._recalc()

    def _validate(self):
        if self.total.value() <= 0:
            QMessageBox.warning(self, "Error", "TotalPrice must be > 0.")
            return
        self.accept()

    def get_data(self):
        return {
            "PatientId": int(self.cmb_patient.currentData()),
            "ServiceId": int(self.cmb_service.currentData()),
            "ProgramId": int(self.cmb_program.currentData()),
            "ServiceDate": self.dt.date().toString("yyyy-MM-dd"),
            "TotalPrice": float(self.total.value()),
            "StateCoveredAmount": float(self.covered.value()),
            "PatientPayableAmount": float(self.payable.value()),
        }

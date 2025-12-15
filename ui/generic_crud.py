# ui/generic_crud.py
from dataclasses import dataclass
from typing import Any, Callable, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QDialog, QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox,
    QComboBox
)
from PyQt6.QtCore import Qt
from sqlalchemy import text
from db import get_engine

engine = get_engine()

@dataclass
class FieldSpec:
    name: str
    label: str
    kind: str = "text"  # "text" | "int" | "decimal" | "fk"
    required: bool = True
    fk_loader: Optional[Callable[[], list[dict]]] = None   # returns rows with id/name keys
    fk_id_key: str = "id"
    fk_name_key: str = "name"

class EditDialog(QDialog):
    def __init__(self, title: str, fields: list[FieldSpec], initial: dict | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(520)
        self.fields = fields
        self.initial = initial or {}
        self.widgets: dict[str, Any] = {}

        layout = QVBoxLayout()
        form = QFormLayout()

        for f in fields:
            w = None
            if f.kind == "text":
                w = QLineEdit()
                w.setText("" if self.initial.get(f.name) is None else str(self.initial.get(f.name)))
            elif f.kind == "int":
                w = QSpinBox()
                w.setRange(-10**9, 10**9)
                v = self.initial.get(f.name)
                w.setValue(int(v) if v not in (None, "") else 0)
            elif f.kind == "decimal":
                w = QDoubleSpinBox()
                w.setRange(-10**12, 10**12)
                w.setDecimals(4)
                v = self.initial.get(f.name)
                w.setValue(float(v) if v not in (None, "") else 0.0)
            elif f.kind == "fk":
                w = QComboBox()
                w.addItem("Select...", None)
                rows = f.fk_loader() if f.fk_loader else []
                for r in rows:
                    w.addItem(str(r[f.fk_name_key]), r[f.fk_id_key])
                cur = self.initial.get(f.name)
                if cur is not None:
                    idx = w.findData(int(cur))
                    if idx >= 0:
                        w.setCurrentIndex(idx)
            else:
                w = QLineEdit()

            self.widgets[f.name] = w
            form.addRow(f.label, w)

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

    def _validate(self):
        for f in self.fields:
            w = self.widgets[f.name]
            if not f.required:
                continue
            if f.kind == "text":
                if not w.text().strip():
                    QMessageBox.warning(self, "Error", f"{f.label} is required.")
                    return
            elif f.kind == "fk":
                if w.currentData() is None:
                    QMessageBox.warning(self, "Error", f"{f.label} is required.")
                    return
        self.accept()

    def get_data(self) -> dict:
        out = {}
        for f in self.fields:
            w = self.widgets[f.name]
            if f.kind == "text":
                out[f.name] = w.text().strip()
            elif f.kind == "int":
                out[f.name] = int(w.value())
            elif f.kind == "decimal":
                out[f.name] = float(w.value())
            elif f.kind == "fk":
                out[f.name] = w.currentData()
            else:
                out[f.name] = None
        return out

class GenericCrudWidget(QWidget):
    """
    Minimal CRUD:
      - list
      - add
      - edit
      - delete hard

    You provide:
      table_name, pk_name, select_columns, fields (for add/edit)
    """
    def __init__(self, table_name: str, pk_name: str, select_columns: list[str], fields: list[FieldSpec], title: str):
        super().__init__()
        self.table_name = table_name
        self.pk_name = pk_name
        self.select_columns = select_columns
        self.fields = fields
        self.title = title

        layout = QVBoxLayout()

        btns = QHBoxLayout()
        self.btn_refresh = QPushButton("Refresh")
        self.btn_add = QPushButton("Add")
        self.btn_edit = QPushButton("Edit Selected")
        self.btn_delete = QPushButton("Delete (Hard)")

        self.btn_refresh.clicked.connect(self.refresh)
        self.btn_add.clicked.connect(self.add_row)
        self.btn_edit.clicked.connect(self.edit_row)
        self.btn_delete.clicked.connect(self.delete_row)

        for b in [self.btn_refresh, self.btn_add, self.btn_edit, self.btn_delete]:
            btns.addWidget(b)
        btns.addStretch(1)
        layout.addLayout(btns)

        self.tbl = QTableWidget(0, len(select_columns))
        self.tbl.setHorizontalHeaderLabels(select_columns)
        self.tbl.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl.verticalHeader().setVisible(False)

        layout.addWidget(self.tbl)
        self.setLayout(layout)

        self.refresh()

    def refresh(self):
        cols = ", ".join(self.select_columns)
        q = text(f"SELECT {cols} FROM {self.table_name} ORDER BY {self.pk_name} DESC")
        with engine.connect() as conn:
            rows = list(conn.execute(q).mappings().all())

        self.tbl.setRowCount(0)
        for r in rows:
            i = self.tbl.rowCount()
            self.tbl.insertRow(i)
            for c, colname in enumerate(self.select_columns):
                val = r.get(colname)
                item = QTableWidgetItem("" if val is None else str(val))
                if colname.lower().endswith("id"):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tbl.setItem(i, c, item)

        self.tbl.resizeColumnsToContents()

    def _selected_pk(self) -> Optional[int]:
        items = self.tbl.selectedItems()
        if not items:
            return None
        row = items[0].row()
        # pk is always first column in our config
        pk_txt = self.tbl.item(row, 0).text()
        return int(pk_txt) if pk_txt else None

    def _selected_row_dict(self) -> Optional[dict]:
        items = self.tbl.selectedItems()
        if not items:
            return None
        row = items[0].row()
        d = {}
        for c, colname in enumerate(self.select_columns):
            d[colname] = self.tbl.item(row, c).text()
        return d

    def add_row(self):
        dlg = EditDialog(f"Add - {self.title}", self.fields, initial=None, parent=self)
        if dlg.exec() != dlg.DialogCode.Accepted:
            return
        data = dlg.get_data()

        cols = ", ".join([f.name for f in self.fields])
        params = ", ".join([f":{f.name}" for f in self.fields])
        q = text(f"INSERT INTO {self.table_name} ({cols}) VALUES ({params})")

        try:
            with engine.begin() as conn:
                conn.execute(q, data)
        except Exception as e:
            QMessageBox.critical(self, "DB Error", f"Insert failed:\n{e}")
            return

        self.refresh()

    def edit_row(self):
        pk = self._selected_pk()
        if not pk:
            QMessageBox.information(self, "Info", "Select a row first.")
            return

        # fetch fresh row from DB (so types are correct)
        cols = ", ".join(self.select_columns)
        q0 = text(f"SELECT {cols} FROM {self.table_name} WHERE {self.pk_name}=:id")
        with engine.connect() as conn:
            row = conn.execute(q0, {"id": pk}).mappings().first()
        if not row:
            QMessageBox.warning(self, "Error", "Row not found.")
            return

        dlg = EditDialog(f"Edit - {self.title}", self.fields, initial=dict(row), parent=self)
        if dlg.exec() != dlg.DialogCode.Accepted:
            return
        data = dlg.get_data()

        set_clause = ", ".join([f"{f.name}=:{f.name}" for f in self.fields])
        q = text(f"UPDATE {self.table_name} SET {set_clause} WHERE {self.pk_name}=:id")
        data["id"] = pk

        try:
            with engine.begin() as conn:
                conn.execute(q, data)
        except Exception as e:
            QMessageBox.critical(self, "DB Error", f"Update failed:\n{e}")
            return

        self.refresh()

    def delete_row(self):
        pk = self._selected_pk()
        if not pk:
            QMessageBox.information(self, "Info", "Select a row first.")
            return
        ok = QMessageBox.question(
            self, "Confirm Delete",
            f"Hard delete {self.title} (Id={pk}) ?\nFK varsa hata verebilir.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if ok != QMessageBox.StandardButton.Yes:
            return

        q = text(f"DELETE FROM {self.table_name} WHERE {self.pk_name}=:id")
        try:
            with engine.begin() as conn:
                conn.execute(q, {"id": pk})
        except Exception as e:
            QMessageBox.critical(self, "DB Error", f"Delete failed:\n{e}")
            return

        self.refresh()

# auth.py
from sqlalchemy import text
from db import get_engine

engine = get_engine()

def login(username: str, password: str):
    q = text("""
        SELECT ua.UserId, ua.RoleId, r.RoleName, ua.StaffId, ua.PatientId,
               ua.PasswordHash, ua.IsActive
        FROM UserAccount ua
        JOIN Role r ON r.RoleId = ua.RoleId
        WHERE ua.Username = :u
    """)

    with engine.connect() as conn:
        row = conn.execute(q, {"u": username}).mappings().first()

    if not row:
        return None
    if not bool(row["IsActive"]):
        return None

    # Şimdilik senin DB’de şifreler düz metin gibi: "1234"
    if str(password) != str(row["PasswordHash"]):
        return None

    return {
        "user_id": row["UserId"],
        "role_id": row["RoleId"],
        "role_name": row["RoleName"],
        "staff_id": row["StaffId"],
        "patient_id": row["PatientId"],
    }

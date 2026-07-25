from datetime import date, datetime

from app import db


# =========================================================
# LỊCH PHÂN CÔNG
# =========================================================

class Schedule(db.Model):

    __tablename__ = "schedules"

    __table_args__ = (
        db.UniqueConstraint(
            "employee_id",
            "work_date",
            "shift",
            name="uq_schedule_employee_date_shift"
        ),
    )

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    employee_id = db.Column(
        db.Integer,
        db.ForeignKey("employees.id"),
        nullable=False
    )

    task_id = db.Column(
        db.Integer,
        db.ForeignKey("tasks.id"),
        nullable=False
    )

    work_date = db.Column(
        db.Date,
        nullable=False
    )

    shift = db.Column(
        db.String(30),
        nullable=False,
        default="Sáng"
    )

    status = db.Column(
        db.String(50),
        nullable=False,
        default="Đã phân công"
    )

    note = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    employee = db.relationship(
        "Employee",
        back_populates="schedules"
    )

    task = db.relationship(
        "Task",
        back_populates="schedules"
    )

    def __repr__(self):
        return (
            f"<Schedule "
            f"{self.employee_id} - "
            f"{self.work_date} - "
            f"{self.shift}>"
        )


# =========================================================
# CHẤM CÔNG
# =========================================================

class Attendance(db.Model):

    __tablename__ = "attendances"

    __table_args__ = (
        db.UniqueConstraint(
            "employee_id",
            "work_date",
            name="uq_attendance_employee_date"
        ),
    )

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    employee_id = db.Column(
        db.Integer,
        db.ForeignKey("employees.id"),
        nullable=False
    )

    work_date = db.Column(
        db.Date,
        nullable=False,
        default=date.today
    )

    check_in = db.Column(
        db.Time,
        nullable=True
    )

    check_out = db.Column(
        db.Time,
        nullable=True
    )

    status = db.Column(
        db.String(50),
        nullable=False,
        default="Đúng giờ"
    )

    note = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    employee = db.relationship(
        "Employee",
        back_populates="attendances"
    )

    def __repr__(self):
        return (
            f"<Attendance "
            f"{self.employee_id} - "
            f"{self.work_date}>"
        )


# =========================================================
# ĐƠN XIN NGHỈ
# =========================================================

class LeaveRequest(db.Model):

    __tablename__ = "leave_requests"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    employee_id = db.Column(
        db.Integer,
        db.ForeignKey("employees.id"),
        nullable=False
    )

    start_date = db.Column(
        db.Date,
        nullable=False
    )

    end_date = db.Column(
        db.Date,
        nullable=False
    )

    leave_type = db.Column(
        db.String(100),
        nullable=False,
        default="Nghỉ phép"
    )

    reason = db.Column(
        db.Text,
        nullable=False
    )

    status = db.Column(
        db.String(50),
        nullable=False,
        default="Chờ duyệt"
    )

    admin_note = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    employee = db.relationship(
        "Employee",
        back_populates="leave_requests"
    )

    def __repr__(self):
        return (
            f"<LeaveRequest "
            f"{self.employee_id} - "
            f"{self.start_date} "
            f"to {self.end_date}>"
        )
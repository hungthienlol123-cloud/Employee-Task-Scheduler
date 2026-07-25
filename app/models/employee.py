from datetime import date

from app import db


class Employee(db.Model):

    __tablename__ = "employees"

    # =====================================================
    # PRIMARY KEY
    # =====================================================

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # =====================================================
    # THÔNG TIN CÁ NHÂN
    # =====================================================

    full_name = db.Column(
        db.String(120),
        nullable=False
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False
    )

    phone = db.Column(
        db.String(30),
        nullable=True
    )

    address = db.Column(
        db.String(255),
        nullable=True
    )

    photo_path = db.Column(
        db.String(255),
        nullable=True
    )

    # =====================================================
    # THÔNG TIN CÔNG VIỆC
    # =====================================================

    department = db.Column(
        db.String(100),
        nullable=False,
        default="Chưa cập nhật"
    )

    position = db.Column(
        db.String(100),
        nullable=True
    )

    hire_date = db.Column(
        db.Date,
        nullable=True,
        default=date.today
    )

    skills = db.Column(
        db.Text,
        nullable=True
    )

    active = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    # =====================================================
    # RELATIONSHIPS
    # =====================================================

    user = db.relationship(
        "User",
        back_populates="employee",
        uselist=False
    )

    schedules = db.relationship(
        "Schedule",
        back_populates="employee",
        cascade="all, delete-orphan"
    )

    attendances = db.relationship(
        "Attendance",
        back_populates="employee",
        cascade="all, delete-orphan"
    )

    leave_requests = db.relationship(
        "LeaveRequest",
        back_populates="employee",
        cascade="all, delete-orphan"
    )

    # =====================================================
    # DISPLAY
    # =====================================================

    def __repr__(self):

        return (
            f"<Employee "
            f"{self.id} - "
            f"{self.full_name}>"
        )
from datetime import datetime

from flask_login import UserMixin

from werkzeug.security import (
    check_password_hash,
    generate_password_hash
)

from app import db


# =========================================================
# USER
# =========================================================

class User(UserMixin, db.Model):

    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(80),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    full_name = db.Column(
        db.String(120),
        nullable=False
    )

    role = db.Column(
        db.String(30),
        nullable=False,
        default="employee"
    )

    employee_id = db.Column(
        db.Integer,
        db.ForeignKey("employees.id"),
        unique=True,
        nullable=True
    )

    admin_code = db.Column(
        db.String(50),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    employee = db.relationship(
        "Employee",
        back_populates="user"
    )

    # -----------------------------------------------------
    # PASSWORD
    # -----------------------------------------------------

    def set_password(self, password):

        self.password_hash = generate_password_hash(
            password
        )

    def check_password(self, password):

        return check_password_hash(
            self.password_hash,
            password
        )

    def __repr__(self):

        return (
            f"<User "
            f"{self.id} - "
            f"{self.username}>"
        )


# =========================================================
# MESSAGE
# =========================================================

class Message(db.Model):

    __tablename__ = "messages"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    sender_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    subject = db.Column(
        db.String(200),
        nullable=False
    )

    content = db.Column(
        db.Text,
        nullable=False
    )

    status = db.Column(
        db.String(50),
        nullable=False,
        default="Chưa đọc"
    )

    admin_reply = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    sender = db.relationship(
        "User",
        foreign_keys=[sender_id]
    )

    def __repr__(self):

        return (
            f"<Message "
            f"{self.id} - "
            f"{self.subject}>"
        )


# =========================================================
# NOTIFICATION
# =========================================================

class Notification(db.Model):

    __tablename__ = "notifications"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    target_role = db.Column(
        db.String(30),
        nullable=False,
        default="all"
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    content = db.Column(
        db.Text,
        nullable=False
    )

    is_read = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    def __repr__(self):

        return (
            f"<Notification "
            f"{self.id} - "
            f"{self.title}>"
        )


# =========================================================
# ACTIVITY LOG
# =========================================================

class ActivityLog(db.Model):

    __tablename__ = "activity_logs"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    action = db.Column(
        db.String(255),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    user = db.relationship(
        "User",
        foreign_keys=[user_id]
    )

    def __repr__(self):

        return (
            f"<ActivityLog "
            f"{self.id} - "
            f"{self.action}>"
        )


# =========================================================
# EMPLOYEE REGISTRATION REQUEST
# =========================================================

class EmployeeRegistrationRequest(db.Model):

    __tablename__ = "employee_registration_requests"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    full_name = db.Column(
        db.String(120),
        nullable=False
    )

    department = db.Column(
        db.String(100),
        nullable=False,
        default="Chưa cập nhật"
    )

    email = db.Column(
        db.String(150),
        nullable=False
    )

    phone = db.Column(
        db.String(30),
        nullable=True
    )

    username = db.Column(
        db.String(80),
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    status = db.Column(
        db.String(50),
        nullable=False,
        default="Chờ duyệt"
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    reviewed_at = db.Column(
        db.DateTime,
        nullable=True
    )

    # -----------------------------------------------------
    # PASSWORD
    # -----------------------------------------------------

    def set_password(self, password):

        self.password_hash = generate_password_hash(
            password
        )

    def check_password(self, password):

        return check_password_hash(
            self.password_hash,
            password
        )

    def __repr__(self):

        return (
            f"<EmployeeRegistrationRequest "
            f"{self.id} - "
            f"{self.username}>"
        )
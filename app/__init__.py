from datetime import date, timedelta
from pathlib import Path

from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from config import Config


# =========================================================
# EXTENSIONS
# =========================================================

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()


# =========================================================
# LOAD USER
# =========================================================

@login_manager.user_loader
def load_user(user_id):
    from app.models import User

    return db.session.get(
        User,
        int(user_id)
    )


# =========================================================
# DỮ LIỆU MẪU
# =========================================================

def seed_data():
    from app.models import (
        Employee,
        Notification,
        Schedule,
        Task,
        User
    )

    # -----------------------------------------------------
    # NHÂN VIÊN
    # -----------------------------------------------------

    if Employee.query.count() == 0:

        employees = [
            Employee(
                full_name="Nguyễn Văn An",
                department="Kỹ thuật",
                email="an@example.com",
                phone="0901000001",
                position="Kỹ thuật viên",
                active=True
            ),

            Employee(
                full_name="Trần Thị Bình",
                department="Kinh doanh",
                email="binh@example.com",
                phone="0901000002",
                position="Chuyên viên",
                active=True
            ),

            Employee(
                full_name="Lê Văn Cường",
                department="Kế toán",
                email="cuong@example.com",
                phone="0901000003",
                position="Kế toán viên",
                active=True
            ),

            Employee(
                full_name="Phạm Thị Dung",
                department="Hành chính",
                email="dung@example.com",
                phone="0901000004",
                position="Nhân viên",
                active=True
            ),

            Employee(
                full_name="Hoàng Văn Đức",
                department="IT",
                email="duc@example.com",
                phone="0901000005",
                position="IT Support",
                active=True
            )
        ]

        db.session.add_all(
            employees
        )

        db.session.flush()

    # -----------------------------------------------------
    # TÀI KHOẢN
    # -----------------------------------------------------

    if User.query.count() == 0:

        admin = User(
            username="admin",
            full_name="Quản trị viên",
            role="admin",
            admin_code="ADM-0001"
        )

        admin.set_password(
            "123456"
        )

        first_employee = (
            Employee.query
            .order_by(Employee.id.asc())
            .first()
        )

        employee_user = User(
            username="nhanvien",
            full_name=first_employee.full_name,
            role="employee",
            employee_id=first_employee.id
        )

        employee_user.set_password(
            "123456"
        )

        db.session.add_all(
            [
                admin,
                employee_user
            ]
        )

    # -----------------------------------------------------
    # CÔNG VIỆC
    # -----------------------------------------------------

    if Task.query.count() == 0:

        tasks = [
            Task(
                task_name="Kiểm tra thiết bị",
                category="Kỹ thuật",
                priority="Cao",
                estimated_hours=4
            ),

            Task(
                task_name="Bảo trì máy móc",
                category="Kỹ thuật",
                priority="Cao",
                estimated_hours=6
            ),

            Task(
                task_name="Tư vấn khách hàng",
                category="Kinh doanh",
                priority="Trung bình",
                estimated_hours=4
            ),

            Task(
                task_name="Nhập dữ liệu",
                category="Kế toán",
                priority="Thấp",
                estimated_hours=4
            ),

            Task(
                task_name="Xử lý văn thư",
                category="Hành chính",
                priority="Trung bình",
                estimated_hours=4
            ),

            Task(
                task_name="Hỗ trợ hệ thống",
                category="IT",
                priority="Cao",
                estimated_hours=4
            )
        ]

        db.session.add_all(
            tasks
        )

        db.session.flush()

    # -----------------------------------------------------
    # LỊCH MẪU
    # -----------------------------------------------------

    if Schedule.query.count() == 0:

        monday = (
            date.today()
            - timedelta(
                days=date.today().weekday()
            )
        )

        employees = (
            Employee.query
            .order_by(Employee.id.asc())
            .limit(4)
            .all()
        )

        tasks = (
            Task.query
            .order_by(Task.id.asc())
            .all()
        )

        if tasks:

            for employee_index, employee in enumerate(
                employees
            ):

                for day_index in range(3):

                    task = tasks[
                        (
                            employee_index
                            + day_index
                        )
                        % len(tasks)
                    ]

                    db.session.add(
                        Schedule(
                            employee_id=employee.id,
                            task_id=task.id,
                            work_date=(
                                monday
                                + timedelta(
                                    days=day_index
                                )
                            ),
                            shift="Sáng",
                            status="Đã phân công"
                        )
                    )

    # -----------------------------------------------------
    # THÔNG BÁO
    # -----------------------------------------------------

    if Notification.query.count() == 0:

        db.session.add_all(
            [
                Notification(
                    target_role="all",
                    title="Chào mừng",
                    content=(
                        "Chào mừng bạn đến "
                        "với WorkFlow VIP."
                    )
                ),

                Notification(
                    target_role="employee",
                    title="Kiểm tra lịch tuần",
                    content=(
                        "Vui lòng kiểm tra "
                        "công việc được giao."
                    )
                )
            ]
        )

    db.session.commit()


# =========================================================
# CREATE APP
# =========================================================

def create_app():

    app = Flask(
        __name__,
        instance_relative_config=True
    )

    app.config.from_object(
        Config
    )

    # -----------------------------------------------------
    # TẠO THƯ MỤC
    # -----------------------------------------------------

    Path(
        app.instance_path
    ).mkdir(
        parents=True,
        exist_ok=True
    )

    Path(
        app.config["UPLOAD_FOLDER"]
    ).mkdir(
        parents=True,
        exist_ok=True
    )

    Path(
        app.config["BACKUP_FOLDER"]
    ).mkdir(
        parents=True,
        exist_ok=True
    )

    # -----------------------------------------------------
    # EXTENSIONS
    # -----------------------------------------------------

    db.init_app(
        app
    )

    login_manager.init_app(
        app
    )

    migrate.init_app(
        app,
        db
    )

    login_manager.login_view = (
        "auth.login"
    )

    login_manager.login_message = (
        "Vui lòng đăng nhập để tiếp tục."
    )

    login_manager.login_message_category = (
        "warning"
    )

    # -----------------------------------------------------
    # LOAD MODELS
    # -----------------------------------------------------

    from app import models

    # -----------------------------------------------------
    # BLUEPRINTS
    # -----------------------------------------------------

    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.employee import employee_bp
    from app.routes.task import task_bp
    from app.routes.schedule import schedule_bp

    app.register_blueprint(
        auth_bp
    )

    app.register_blueprint(
        dashboard_bp
    )

    app.register_blueprint(
        employee_bp
    )

    app.register_blueprint(
        task_bp
    )

    app.register_blueprint(
        schedule_bp
    )

    # -----------------------------------------------------
    # DATABASE
    # -----------------------------------------------------

    with app.app_context():

        db.create_all()

        seed_data()

    return app
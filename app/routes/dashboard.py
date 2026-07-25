import csv
import io
from datetime import date

from flask import (
    Blueprint,
    Response,
    flash,
    redirect,
    render_template,
    request,
    url_for
)

from flask_login import (
    current_user,
    login_required
)

from app import db

from app.models import (
    ActivityLog,
    Employee,
    Message,
    Notification,
    Schedule,
    Task
)

from app.routes import admin_required

from app.services import backup_database


# =========================================================
# BLUEPRINT
# =========================================================

dashboard_bp = Blueprint(
    "dashboard",
    __name__
)


# =========================================================
# DASHBOARD CHUNG
# =========================================================

@dashboard_bp.route("/dashboard")
@login_required
def home():

    if current_user.role == "admin":

        return redirect(
            url_for("dashboard.admin")
        )

    return redirect(
        url_for("dashboard.employee")
    )


# =========================================================
# DASHBOARD ADMIN
# =========================================================

@dashboard_bp.route("/dashboard/admin")
@login_required
@admin_required
def admin():

    today = date.today()

    stats = {
        "employees": (
            Employee.query
            .filter_by(active=True)
            .count()
        ),

        "tasks": (
            Task.query.count()
        ),

        "today": (
            Schedule.query
            .filter(
                Schedule.work_date == today
            )
            .count()
        ),

        "messages": (
            Message.query
            .filter_by(
                status="Chưa đọc"
            )
            .count()
        )
    }

    # -----------------------------------------------------
    # KHỐI LƯỢNG CÔNG VIỆC
    # -----------------------------------------------------

    active_employees = (
        Employee.query
        .filter_by(active=True)
        .order_by(
            Employee.full_name.asc()
        )
        .all()
    )

    workload = []

    for employee in active_employees:

        total = (
            Schedule.query
            .filter(
                Schedule.employee_id
                == employee.id,

                Schedule.status
                != "Hoàn thành"
            )
            .count()
        )

        workload.append(
            (
                employee,
                total
            )
        )

    # -----------------------------------------------------
    # NHẬT KÝ
    # -----------------------------------------------------

    logs = (
        ActivityLog.query
        .order_by(
            ActivityLog.created_at.desc()
        )
        .limit(8)
        .all()
    )

    return render_template(
        "dashboard/admin.html",
        stats=stats,
        workload=workload,
        logs=logs,
        now=today.strftime("%d/%m/%Y")
    )


# =========================================================
# DASHBOARD NHÂN VIÊN
# =========================================================

@dashboard_bp.route("/dashboard/employee")
@login_required
def employee():

    if current_user.role != "employee":

        return redirect(
            url_for("dashboard.admin")
        )

    employee_data = current_user.employee

    if not employee_data:

        flash(
            "Tài khoản chưa được liên kết "
            "với hồ sơ nhân viên.",
            "warning"
        )

        return render_template(
            "dashboard/employee.html",
            employee=None,
            stats={
                "today": 0,
                "pending": 0,
                "messages": 0
            },
            recent=[]
        )

    today = date.today()

    stats = {
        "today": (
            Schedule.query
            .filter(
                Schedule.employee_id
                == employee_data.id,

                Schedule.work_date
                == today
            )
            .count()
        ),

        "pending": (
            Schedule.query
            .filter(
                Schedule.employee_id
                == employee_data.id,

                Schedule.status
                != "Hoàn thành"
            )
            .count()
        ),

        "messages": (
            Message.query
            .filter(
                Message.sender_id
                == current_user.id
            )
            .count()
        )
    }

    recent = (
        Schedule.query
        .filter(
            Schedule.employee_id
            == employee_data.id
        )
        .order_by(
            Schedule.work_date.desc()
        )
        .limit(6)
        .all()
    )

    return render_template(
        "dashboard/employee.html",
        employee=employee_data,
        stats=stats,
        recent=recent
    )


# =========================================================
# THÔNG BÁO
# =========================================================

@dashboard_bp.route(
    "/notifications",
    methods=["GET", "POST"]
)
@login_required
def notifications():

    if request.method == "POST":

        if current_user.role != "admin":

            flash(
                "Bạn không có quyền "
                "tạo thông báo.",
                "danger"
            )

            return redirect(
                url_for(
                    "dashboard.notifications"
                )
            )

        title = (
            request.form
            .get("title", "")
            .strip()
        )

        content = (
            request.form
            .get("content", "")
            .strip()
        )

        target_role = (
            request.form
            .get(
                "target_role",
                "all"
            )
            .strip()
        )

        if target_role not in {
            "all",
            "admin",
            "employee"
        }:
            target_role = "all"

        if not title or not content:

            flash(
                "Vui lòng nhập tiêu đề "
                "và nội dung.",
                "warning"
            )

            return redirect(
                url_for(
                    "dashboard.notifications"
                )
            )

        notification = Notification(
            target_role=target_role,
            title=title,
            content=content,
            is_read=False
        )

        db.session.add(
            notification
        )

        db.session.add(
            ActivityLog(
                user_id=current_user.id,
                action=(
                    "Tạo thông báo: "
                    f"{title}"
                )
            )
        )

        db.session.commit()

        flash(
            "Đã đăng thông báo.",
            "success"
        )

        return redirect(
            url_for(
                "dashboard.notifications"
            )
        )

    # -----------------------------------------------------
    # DANH SÁCH THÔNG BÁO
    # -----------------------------------------------------

    if current_user.role == "admin":

        items = (
            Notification.query
            .filter(
                Notification.target_role.in_(
                    [
                        "all",
                        "admin"
                    ]
                )
            )
            .order_by(
                Notification.created_at.desc()
            )
            .all()
        )

    else:

        items = (
            Notification.query
            .filter(
                Notification.target_role.in_(
                    [
                        "all",
                        "employee"
                    ]
                )
            )
            .order_by(
                Notification.created_at.desc()
            )
            .all()
        )

    return render_template(
        "common/notifications.html",
        items=items
    )


# =========================================================
# ĐÁNH DẤU THÔNG BÁO ĐÃ ĐỌC
# =========================================================

@dashboard_bp.post(
    "/notifications/<int:notification_id>/read"
)
@login_required
def mark_notification_read(
    notification_id
):

    notification = db.session.get(
        Notification,
        notification_id
    )

    if not notification:

        flash(
            "Không tìm thấy thông báo.",
            "warning"
        )

        return redirect(
            url_for(
                "dashboard.notifications"
            )
        )

    notification.is_read = True

    db.session.commit()

    return redirect(
        url_for(
            "dashboard.notifications"
        )
    )


# =========================================================
# LIÊN HỆ
# =========================================================

@dashboard_bp.route(
    "/contact",
    methods=["GET", "POST"]
)
@login_required
def contact():

    # -----------------------------------------------------
    # NHÂN VIÊN GỬI TIN
    # -----------------------------------------------------

    if request.method == "POST":

        if current_user.role != "employee":

            flash(
                "Chỉ nhân viên mới "
                "gửi yêu cầu theo cách này.",
                "warning"
            )

            return redirect(
                url_for(
                    "dashboard.contact"
                )
            )

        subject = (
            request.form
            .get("subject", "")
            .strip()
        )

        content = (
            request.form
            .get("content", "")
            .strip()
        )

        if not subject or not content:

            flash(
                "Vui lòng nhập chủ đề "
                "và nội dung.",
                "warning"
            )

            return redirect(
                url_for(
                    "dashboard.contact"
                )
            )

        message = Message(
            sender_id=current_user.id,
            subject=subject,
            content=content,
            status="Chưa đọc"
        )

        db.session.add(
            message
        )

        db.session.commit()

        flash(
            "Đã gửi yêu cầu tới Admin.",
            "success"
        )

        return redirect(
            url_for(
                "dashboard.contact"
            )
        )

    # -----------------------------------------------------
    # ADMIN XEM TOÀN BỘ
    # -----------------------------------------------------

    if current_user.role == "admin":

        messages = (
            Message.query
            .order_by(
                Message.created_at.desc()
            )
            .all()
        )

        changed = False

        for message in messages:

            if message.status == "Chưa đọc":

                message.status = "Đã đọc"

                changed = True

        if changed:

            db.session.commit()

    # -----------------------------------------------------
    # NHÂN VIÊN XEM TIN CỦA MÌNH
    # -----------------------------------------------------

    else:

        messages = (
            Message.query
            .filter(
                Message.sender_id
                == current_user.id
            )
            .order_by(
                Message.created_at.desc()
            )
            .all()
        )

    return render_template(
        "common/contact.html",
        messages=messages
    )


# =========================================================
# ADMIN TRẢ LỜI TIN NHẮN
# =========================================================

@dashboard_bp.post(
    "/contact/<int:message_id>/reply"
)
@login_required
@admin_required
def reply_message(
    message_id
):

    message = db.session.get(
        Message,
        message_id
    )

    if not message:

        flash(
            "Không tìm thấy tin nhắn.",
            "warning"
        )

        return redirect(
            url_for(
                "dashboard.contact"
            )
        )

    reply = (
        request.form
        .get("reply", "")
        .strip()
    )

    if not reply:

        flash(
            "Vui lòng nhập nội dung phản hồi.",
            "warning"
        )

        return redirect(
            url_for(
                "dashboard.contact"
            )
        )

    message.admin_reply = reply

    message.status = "Đã trả lời"

    db.session.add(
        ActivityLog(
            user_id=current_user.id,
            action=(
                "Phản hồi tin nhắn "
                f"#{message.id}"
            )
        )
    )

    db.session.commit()

    flash(
        "Đã phản hồi nhân viên.",
        "success"
    )

    return redirect(
        url_for(
            "dashboard.contact"
        )
    )


# =========================================================
# BÁO CÁO
# =========================================================

@dashboard_bp.route("/reports")
@login_required
@admin_required
def reports():

    completed = (
        Schedule.query
        .filter(
            Schedule.status
            == "Hoàn thành"
        )
        .count()
    )

    pending = (
        Schedule.query
        .filter(
            Schedule.status
            != "Hoàn thành"
        )
        .count()
    )

    return render_template(
        "common/reports.html",
        completed=completed,
        pending=pending
    )


# =========================================================
# EXPORT CSV
# =========================================================

@dashboard_bp.route(
    "/reports/export/<string:kind>"
)
@login_required
@admin_required
def export_csv(kind):

    output = io.StringIO()

    writer = csv.writer(
        output
    )

    # -----------------------------------------------------
    # EMPLOYEES
    # -----------------------------------------------------

    if kind == "employees":

        writer.writerow(
            [
                "ID",
                "Họ tên",
                "Phòng ban",
                "Email",
                "Điện thoại",
                "Chức vụ",
                "Trạng thái"
            ]
        )

        employees = (
            Employee.query
            .order_by(
                Employee.id.asc()
            )
            .all()
        )

        for employee in employees:

            writer.writerow(
                [
                    employee.id,
                    employee.full_name,
                    employee.department,
                    employee.email,
                    employee.phone or "",
                    employee.position or "",
                    (
                        "Đang làm"
                        if employee.active
                        else "Ngừng hoạt động"
                    )
                ]
            )

        filename = (
            "employees.csv"
        )

    # -----------------------------------------------------
    # TASKS
    # -----------------------------------------------------

    elif kind == "tasks":

        writer.writerow(
            [
                "ID",
                "Tên công việc",
                "Nhóm",
                "Ưu tiên",
                "Giờ dự kiến",
                "Mô tả"
            ]
        )

        tasks = (
            Task.query
            .order_by(
                Task.id.asc()
            )
            .all()
        )

        for task in tasks:

            writer.writerow(
                [
                    task.id,
                    task.task_name,
                    task.category or "",
                    task.priority,
                    task.estimated_hours,
                    task.description or ""
                ]
            )

        filename = (
            "tasks.csv"
        )

    # -----------------------------------------------------
    # SCHEDULES
    # -----------------------------------------------------

    elif kind == "schedules":

        writer.writerow(
            [
                "ID",
                "Ngày",
                "Nhân viên",
                "Công việc",
                "Ca",
                "Trạng thái",
                "Ghi chú"
            ]
        )

        schedules = (
            Schedule.query
            .order_by(
                Schedule.work_date.asc()
            )
            .all()
        )

        for item in schedules:

            writer.writerow(
                [
                    item.id,
                    item.work_date.strftime(
                        "%d/%m/%Y"
                    ),
                    item.employee.full_name,
                    item.task.task_name,
                    item.shift,
                    item.status,
                    item.note or ""
                ]
            )

        filename = (
            "schedules.csv"
        )

    else:

        flash(
            "Loại báo cáo không hợp lệ.",
            "danger"
        )

        return redirect(
            url_for(
                "dashboard.reports"
            )
        )

    # -----------------------------------------------------
    # UTF-8 BOM CHO EXCEL
    # -----------------------------------------------------

    csv_data = (
        "\ufeff"
        + output.getvalue()
    )

    output.close()

    return Response(
        csv_data,
        mimetype=(
            "text/csv; "
            "charset=utf-8"
        ),
        headers={
            "Content-Disposition":
                (
                    "attachment; "
                    f"filename={filename}"
                )
        }
    )


# =========================================================
# BACKUP SQLITE
# =========================================================

@dashboard_bp.post(
    "/reports/backup"
)
@login_required
@admin_required
def backup():

    try:

        backup_path = (
            backup_database()
        )

        db.session.add(
            ActivityLog(
                user_id=current_user.id,
                action=(
                    "Sao lưu cơ sở dữ liệu"
                )
            )
        )

        db.session.commit()

        flash(
            (
                "Sao lưu thành công: "
                f"{backup_path}"
            ),
            "success"
        )

    except Exception as exc:

        db.session.rollback()

        flash(
            (
                "Không thể sao lưu database: "
                f"{exc}"
            ),
            "danger"
        )

    return redirect(
        url_for(
            "dashboard.reports"
        )
    )


# =========================================================
# CÀI ĐẶT
# =========================================================

@dashboard_bp.route(
    "/settings",
    methods=["GET", "POST"]
)
@login_required
def settings():

    if request.method == "POST":

        old_password = (
            request.form
            .get("old_password", "")
        )

        new_password = (
            request.form
            .get("new_password", "")
        )

        confirm_password = (
            request.form
            .get("confirm_password", "")
        )

        # -------------------------------------------------
        # MẬT KHẨU HIỆN TẠI
        # -------------------------------------------------

        if not current_user.check_password(
            old_password
        ):

            flash(
                "Mật khẩu hiện tại "
                "không chính xác.",
                "danger"
            )

            return redirect(
                url_for(
                    "dashboard.settings"
                )
            )

        # -------------------------------------------------
        # ĐỘ DÀI
        # -------------------------------------------------

        if len(new_password) < 6:

            flash(
                "Mật khẩu mới phải có "
                "ít nhất 6 ký tự.",
                "warning"
            )

            return redirect(
                url_for(
                    "dashboard.settings"
                )
            )

        # -------------------------------------------------
        # CONFIRM
        # -------------------------------------------------

        if (
            new_password
            != confirm_password
        ):

            flash(
                "Hai mật khẩu mới "
                "không khớp.",
                "warning"
            )

            return redirect(
                url_for(
                    "dashboard.settings"
                )
            )

        current_user.set_password(
            new_password
        )

        db.session.add(
            ActivityLog(
                user_id=current_user.id,
                action="Đổi mật khẩu"
            )
        )

        db.session.commit()

        flash(
            "Đổi mật khẩu thành công.",
            "success"
        )

        return redirect(
            url_for(
                "dashboard.settings"
            )
        )

    return render_template(
        "common/settings.html"
    )
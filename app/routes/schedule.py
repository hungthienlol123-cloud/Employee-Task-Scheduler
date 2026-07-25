from datetime import date, datetime, time, timedelta

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from flask_login import (
    current_user,
    login_required,
)

from app import db

from app.models import (
    ActivityLog,
    Attendance,
    Employee,
    LeaveRequest,
    Schedule,
    Task,
)

from app.routes import (
    admin_required,
    employee_required,
)

from app.services import auto_assign


# =========================================================
# BLUEPRINT
# =========================================================

schedule_bp = Blueprint(
    "schedule",
    __name__,
    url_prefix="/schedule",
)


# =========================================================
# ADMIN - DANH SÁCH PHÂN CÔNG
# =========================================================

@schedule_bp.route("/")
@login_required
@admin_required
def index():

    schedules = (
        Schedule.query
        .order_by(
            Schedule.work_date.desc(),
            Schedule.shift.asc(),
        )
        .all()
    )

    employees = (
        Employee.query
        .filter_by(active=True)
        .order_by(
            Employee.full_name.asc()
        )
        .all()
    )

    tasks = (
        Task.query
        .order_by(
            Task.task_name.asc()
        )
        .all()
    )

    return render_template(
        "schedule/list.html",
        schedules=schedules,
        employees=employees,
        tasks=tasks,
    )


# =========================================================
# ADMIN - PHÂN CÔNG THỦ CÔNG
# =========================================================

@schedule_bp.post("/assign")
@login_required
@admin_required
def assign():

    employee_id = request.form.get(
        "employee_id",
        type=int,
    )

    task_id = request.form.get(
        "task_id",
        type=int,
    )

    work_date_text = (
        request.form
        .get("work_date", "")
        .strip()
    )

    shift = (
        request.form
        .get("shift", "Sáng")
        .strip()
    )

    note = (
        request.form
        .get("note", "")
        .strip()
    )

    if (
        not employee_id
        or not task_id
        or not work_date_text
    ):

        flash(
            "Vui lòng nhập đầy đủ thông tin phân công.",
            "warning",
        )

        return redirect(
            url_for("schedule.index")
        )

    try:

        work_date = date.fromisoformat(
            work_date_text
        )

    except ValueError:

        flash(
            "Ngày làm việc không hợp lệ.",
            "warning",
        )

        return redirect(
            url_for("schedule.index")
        )

    if shift not in {
        "Sáng",
        "Chiều",
    }:
        shift = "Sáng"

    employee = db.session.get(
        Employee,
        employee_id,
    )

    task = db.session.get(
        Task,
        task_id,
    )

    if employee is None or task is None:

        flash(
            "Nhân viên hoặc công việc không tồn tại.",
            "danger",
        )

        return redirect(
            url_for("schedule.index")
        )

    if not employee.active:

        flash(
            "Nhân viên này đang ngừng hoạt động.",
            "warning",
        )

        return redirect(
            url_for("schedule.index")
        )

    # =====================================================
    # KIỂM TRA NGHỈ PHÉP
    # =====================================================

    leave_request = (
        LeaveRequest.query
        .filter(
            LeaveRequest.employee_id
            == employee.id,

            LeaveRequest.status
            == "Đã duyệt",

            LeaveRequest.start_date
            <= work_date,

            LeaveRequest.end_date
            >= work_date,
        )
        .first()
    )

    if leave_request:

        flash(
            "Nhân viên đang nghỉ phép trong ngày đã chọn.",
            "warning",
        )

        return redirect(
            url_for("schedule.index")
        )

    # =====================================================
    # TÌM LỊCH CÙNG NGÀY / CA
    # =====================================================

    existing = (
        Schedule.query
        .filter(
            Schedule.employee_id
            == employee.id,

            Schedule.work_date
            == work_date,

            Schedule.shift
            == shift,
        )
        .first()
    )

    if existing:

        existing.task_id = task.id
        existing.note = note or None
        existing.status = "Đã phân công"

        message = (
            "Đã cập nhật phân công hiện có."
        )

    else:

        schedule = Schedule(
            employee_id=employee.id,
            task_id=task.id,
            work_date=work_date,
            shift=shift,
            status="Đã phân công",
            note=note or None,
        )

        db.session.add(schedule)

        message = (
            "Đã phân công công việc."
        )

    db.session.add(
        ActivityLog(
            user_id=current_user.id,
            action=(
                "Phân công "
                f"{task.task_name} "
                f"cho {employee.full_name}"
            ),
        )
    )

    db.session.commit()

    flash(
        message,
        "success",
    )

    return redirect(
        url_for("schedule.index")
    )


# =========================================================
# ADMIN - CẬP NHẬT TRẠNG THÁI
# =========================================================

@schedule_bp.post(
    "/<int:schedule_id>/status"
)
@login_required
@admin_required
def update_status(schedule_id):

    item = db.session.get(
        Schedule,
        schedule_id,
    )

    if item is None:

        flash(
            "Không tìm thấy phân công.",
            "warning",
        )

        return redirect(
            url_for("schedule.index")
        )

    status = (
        request.form
        .get("status", "")
        .strip()
    )

    allowed_statuses = {
        "Đã phân công",
        "Đang thực hiện",
        "Hoàn thành",
        "Tạm hoãn",
    }

    if status not in allowed_statuses:

        flash(
            "Trạng thái không hợp lệ.",
            "warning",
        )

        return redirect(
            url_for("schedule.index")
        )

    item.status = status

    db.session.commit()

    flash(
        "Đã cập nhật trạng thái.",
        "success",
    )

    return redirect(
        url_for("schedule.index")
    )


# =========================================================
# ADMIN - XÓA PHÂN CÔNG
# =========================================================

@schedule_bp.post(
    "/<int:schedule_id>/delete"
)
@login_required
@admin_required
def delete(schedule_id):

    item = db.session.get(
        Schedule,
        schedule_id,
    )

    if item is None:

        flash(
            "Không tìm thấy phân công.",
            "warning",
        )

        return redirect(
            url_for("schedule.index")
        )

    db.session.delete(item)

    db.session.commit()

    flash(
        "Đã xóa phân công.",
        "success",
    )

    return redirect(
        url_for("schedule.index")
    )


# =========================================================
# ADMIN - PHÂN CÔNG TỰ ĐỘNG
# =========================================================

@schedule_bp.route(
    "/auto",
    methods=["GET", "POST"],
)
@login_required
@admin_required
def auto():

    assigned = None

    if request.method == "POST":

        work_date_text = (
            request.form
            .get("work_date", "")
            .strip()
        )

        shift = (
            request.form
            .get("shift", "Sáng")
            .strip()
        )

        limit = request.form.get(
            "limit",
            5,
        )

        if not work_date_text:

            flash(
                "Vui lòng chọn ngày làm việc.",
                "warning",
            )

            return render_template(
                "schedule/auto.html",
                assigned=assigned,
            )

        try:

            work_date = date.fromisoformat(
                work_date_text
            )

        except ValueError:

            flash(
                "Ngày làm việc không hợp lệ.",
                "warning",
            )

            return render_template(
                "schedule/auto.html",
                assigned=assigned,
            )

        try:

            assigned = auto_assign(
                work_date=work_date,
                shift=shift,
                limit=limit,
            )

            if assigned:

                db.session.add(
                    ActivityLog(
                        user_id=current_user.id,
                        action=(
                            "Phân công tự động "
                            f"{len(assigned)} nhân viên"
                        ),
                    )
                )

                db.session.commit()

                flash(
                    (
                        "Đã phân công tự động "
                        f"{len(assigned)} nhân viên."
                    ),
                    "success",
                )

            else:

                flash(
                    "Không có nhân viên phù hợp để phân công.",
                    "info",
                )

        except Exception as exc:

            db.session.rollback()

            flash(
                f"Phân công tự động thất bại: {exc}",
                "danger",
            )

    return render_template(
        "schedule/auto.html",
        assigned=assigned,
    )


# =========================================================
# LỊCH TUẦN
# =========================================================

@schedule_bp.route("/week")
@login_required
def week():

    today = date.today()

    monday = (
        today
        - timedelta(
            days=today.weekday()
        )
    )

    days = [
        monday
        + timedelta(days=index)
        for index in range(6)
    ]

    if current_user.role == "admin":

        employees = (
            Employee.query
            .filter_by(active=True)
            .order_by(
                Employee.full_name.asc()
            )
            .all()
        )

    else:

        if current_user.employee is None:

            employees = []

        else:

            employees = [
                current_user.employee
            ]

    matrix = {}

    for employee in employees:

        matrix[
            employee.id
        ] = {}

        for day in days:

            items = (
                Schedule.query
                .filter(
                    Schedule.employee_id
                    == employee.id,

                    Schedule.work_date
                    == day,
                )
                .order_by(
                    Schedule.shift.asc()
                )
                .all()
            )

            matrix[
                employee.id
            ][day] = items

    return render_template(
        "schedule/week.html",
        employees=employees,
        days=days,
        matrix=matrix,
    )


# =========================================================
# NHÂN VIÊN - CÔNG VIỆC CỦA TÔI
# =========================================================

@schedule_bp.route("/mine")
@login_required
@employee_required
def mine():

    employee = current_user.employee

    if employee is None:

        flash(
            "Tài khoản chưa liên kết với nhân viên.",
            "warning",
        )

        schedules = []

    else:

        schedules = (
            Schedule.query
            .filter(
                Schedule.employee_id
                == employee.id
            )
            .order_by(
                Schedule.work_date.desc(),
                Schedule.shift.asc(),
            )
            .all()
        )

    return render_template(
        "schedule/my.html",
        schedules=schedules,
    )


# =========================================================
# NHÂN VIÊN - HOÀN THÀNH CÔNG VIỆC
# =========================================================

@schedule_bp.post(
    "/<int:schedule_id>/complete"
)
@login_required
@employee_required
def complete(schedule_id):

    employee = current_user.employee

    if employee is None:

        flash(
            "Tài khoản chưa liên kết với nhân viên.",
            "warning",
        )

        return redirect(
            url_for("schedule.mine")
        )

    item = (
        Schedule.query
        .filter(
            Schedule.id
            == schedule_id,

            Schedule.employee_id
            == employee.id,
        )
        .first()
    )

    if item is None:

        flash(
            "Không tìm thấy công việc.",
            "warning",
        )

        return redirect(
            url_for("schedule.mine")
        )

    item.status = "Hoàn thành"

    db.session.commit()

    flash(
        "Đã xác nhận hoàn thành công việc.",
        "success",
    )

    return redirect(
        url_for("schedule.mine")
    )


# =========================================================
# NHÂN VIÊN - CHẤM CÔNG
# =========================================================

@schedule_bp.route(
    "/attendance/employee",
    methods=["GET", "POST"],
)
@login_required
@employee_required
def attendance_employee():

    employee = current_user.employee

    if employee is None:

        flash(
            "Tài khoản chưa liên kết với nhân viên.",
            "warning",
        )

        return redirect(
            url_for(
                "dashboard.employee"
            )
        )

    today = date.today()

    record = (
        Attendance.query
        .filter(
            Attendance.employee_id
            == employee.id,

            Attendance.work_date
            == today,
        )
        .first()
    )

    if request.method == "POST":

        action = (
            request.form
            .get("action", "")
            .strip()
        )

        now = datetime.now()

        # =================================================
        # CHECK IN
        # =================================================

        if action == "in":

            if record and record.check_in:

                flash(
                    "Bạn đã chấm công vào hôm nay.",
                    "info",
                )

                return redirect(
                    url_for(
                        "schedule.attendance_employee"
                    )
                )

            if record is None:

                record = Attendance(
                    employee_id=employee.id,
                    work_date=today,
                )

                db.session.add(record)

            record.check_in = (
                now.time()
                .replace(
                    microsecond=0
                )
            )

            late_time = time(
                8,
                15,
                0,
            )

            if record.check_in > late_time:

                record.status = (
                    "Đi trễ"
                )

            else:

                record.status = (
                    "Đúng giờ"
                )

            db.session.commit()

            flash(
                "Check-in thành công.",
                "success",
            )

        # =================================================
        # CHECK OUT
        # =================================================

        elif action == "out":

            if (
                record is None
                or record.check_in is None
            ):

                flash(
                    "Bạn phải check-in trước.",
                    "warning",
                )

                return redirect(
                    url_for(
                        "schedule.attendance_employee"
                    )
                )

            if record.check_out:

                flash(
                    "Bạn đã check-out hôm nay.",
                    "info",
                )

                return redirect(
                    url_for(
                        "schedule.attendance_employee"
                    )
                )

            record.check_out = (
                now.time()
                .replace(
                    microsecond=0
                )
            )

            db.session.commit()

            flash(
                "Check-out thành công.",
                "success",
            )

        else:

            flash(
                "Thao tác chấm công không hợp lệ.",
                "warning",
            )

        return redirect(
            url_for(
                "schedule.attendance_employee"
            )
        )

    history = (
        Attendance.query
        .filter(
            Attendance.employee_id
            == employee.id
        )
        .order_by(
            Attendance.work_date.desc()
        )
        .limit(30)
        .all()
    )

    return render_template(
        "schedule/attendance_employee.html",
        record=record,
        history=history,
    )


# =========================================================
# ADMIN - XEM CHẤM CÔNG
# =========================================================

@schedule_bp.route(
    "/attendance/admin"
)
@login_required
@admin_required
def attendance_admin():

    selected_date_text = (
        request.args
        .get(
            "date",
            date.today().isoformat(),
        )
        .strip()
    )

    try:

        selected_date = date.fromisoformat(
            selected_date_text
        )

    except ValueError:

        selected_date = date.today()

        selected_date_text = (
            selected_date.isoformat()
        )

    employees = (
        Employee.query
        .filter_by(active=True)
        .order_by(
            Employee.full_name.asc()
        )
        .all()
    )

    records = (
        Attendance.query
        .filter(
            Attendance.work_date
            == selected_date
        )
        .all()
    )

    attendance = {
        item.employee_id: item
        for item in records
    }

    return render_template(
        "schedule/attendance_admin.html",
        employees=employees,
        attendance=attendance,
        selected_date=selected_date_text,
    )


# =========================================================
# NHÂN VIÊN - XIN NGHỈ
# =========================================================

@schedule_bp.route(
    "/leave/employee",
    methods=["GET", "POST"],
)
@login_required
@employee_required
def leave_employee():

    employee = current_user.employee

    if employee is None:

        flash(
            "Tài khoản chưa liên kết với nhân viên.",
            "warning",
        )

        return redirect(
            url_for(
                "dashboard.employee"
            )
        )

    if request.method == "POST":

        start_date_text = (
            request.form
            .get("start_date", "")
            .strip()
        )

        end_date_text = (
            request.form
            .get("end_date", "")
            .strip()
        )

        leave_type = (
            request.form
            .get(
                "leave_type",
                "Nghỉ phép",
            )
            .strip()
        )

        reason = (
            request.form
            .get("reason", "")
            .strip()
        )

        if (
            not start_date_text
            or not end_date_text
            or not reason
        ):

            flash(
                "Vui lòng nhập đầy đủ thông tin.",
                "warning",
            )

            return redirect(
                url_for(
                    "schedule.leave_employee"
                )
            )

        try:

            start_date = date.fromisoformat(
                start_date_text
            )

            end_date = date.fromisoformat(
                end_date_text
            )

        except ValueError:

            flash(
                "Ngày nghỉ không hợp lệ.",
                "warning",
            )

            return redirect(
                url_for(
                    "schedule.leave_employee"
                )
            )

        if end_date < start_date:

            flash(
                "Ngày kết thúc phải từ ngày bắt đầu trở đi.",
                "warning",
            )

            return redirect(
                url_for(
                    "schedule.leave_employee"
                )
            )

        leave_request = LeaveRequest(
            employee_id=employee.id,
            start_date=start_date,
            end_date=end_date,
            leave_type=leave_type,
            reason=reason,
            status="Chờ duyệt",
        )

        db.session.add(
            leave_request
        )

        db.session.commit()

        flash(
            "Đã gửi đơn xin nghỉ.",
            "success",
        )

        return redirect(
            url_for(
                "schedule.leave_employee"
            )
        )

    items = (
        LeaveRequest.query
        .filter(
            LeaveRequest.employee_id
            == employee.id
        )
        .order_by(
            LeaveRequest.created_at.desc()
        )
        .all()
    )

    return render_template(
        "schedule/leave_employee.html",
        items=items,
    )


# =========================================================
# ADMIN - QUẢN LÝ ĐƠN NGHỈ
# =========================================================

@schedule_bp.route(
    "/leave/admin"
)
@login_required
@admin_required
def leave_admin():

    items = (
        LeaveRequest.query
        .order_by(
            LeaveRequest.created_at.desc()
        )
        .all()
    )

    return render_template(
        "schedule/leave_admin.html",
        items=items,
    )


# =========================================================
# ADMIN - DUYỆT / TỪ CHỐI NGHỈ
# =========================================================

@schedule_bp.post(
    "/leave/<int:request_id>/review"
)
@login_required
@admin_required
def review_leave(request_id):

    item = db.session.get(
        LeaveRequest,
        request_id,
    )

    if item is None:

        flash(
            "Không tìm thấy đơn nghỉ.",
            "warning",
        )

        return redirect(
            url_for(
                "schedule.leave_admin"
            )
        )

    status = (
        request.form
        .get("status", "")
        .strip()
    )

    admin_note = (
        request.form
        .get("admin_note", "")
        .strip()
    )

    if status not in {
        "Đã duyệt",
        "Từ chối",
    }:

        flash(
            "Trạng thái xử lý không hợp lệ.",
            "warning",
        )

        return redirect(
            url_for(
                "schedule.leave_admin"
            )
        )

    item.status = status
    item.admin_note = admin_note or None

    db.session.add(
        ActivityLog(
            user_id=current_user.id,
            action=(
                f"{status} đơn nghỉ "
                f"của {item.employee.full_name}"
            ),
        )
    )

    db.session.commit()

    flash(
        (
            "Đã duyệt đơn nghỉ."
            if status == "Đã duyệt"
            else "Đã từ chối đơn nghỉ."
        ),
        "success",
    )

    return redirect(
        url_for(
            "schedule.leave_admin"
        )
    )
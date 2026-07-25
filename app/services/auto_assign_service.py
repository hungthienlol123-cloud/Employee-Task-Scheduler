from datetime import date

from app import db
from app.models import (
    Employee,
    LeaveRequest,
    Schedule,
    Task,
)


# =========================================================
# THỨ TỰ ƯU TIÊN
# =========================================================

PRIORITY_ORDER = {
    "Cao": 1,
    "Trung bình": 2,
    "Thấp": 3,
}


# =========================================================
# KHỐI LƯỢNG CÔNG VIỆC CỦA NHÂN VIÊN
# =========================================================

def get_employee_workload(
    employee_id,
    work_date
):

    return (
        Schedule.query
        .filter(
            Schedule.employee_id == employee_id,
            Schedule.work_date >= work_date,
            Schedule.status != "Hoàn thành",
        )
        .count()
    )


# =========================================================
# KIỂM TRA NGHỈ PHÉP
# =========================================================

def employee_on_leave(
    employee_id,
    work_date
):

    leave = (
        LeaveRequest.query
        .filter(
            LeaveRequest.employee_id == employee_id,
            LeaveRequest.status == "Đã duyệt",
            LeaveRequest.start_date <= work_date,
            LeaveRequest.end_date >= work_date,
        )
        .first()
    )

    return leave is not None


# =========================================================
# KIỂM TRA NHÂN VIÊN ĐÃ CÓ LỊCH
# =========================================================

def employee_has_schedule(
    employee_id,
    work_date,
    shift
):

    schedule = (
        Schedule.query
        .filter(
            Schedule.employee_id == employee_id,
            Schedule.work_date == work_date,
            Schedule.shift == shift,
        )
        .first()
    )

    return schedule is not None


# =========================================================
# LẤY NHÂN VIÊN CÓ THỂ PHÂN CÔNG
# =========================================================

def get_available_employees(
    work_date,
    shift
):

    employees = (
        Employee.query
        .filter_by(active=True)
        .order_by(Employee.full_name.asc())
        .all()
    )

    available = []

    for employee in employees:

        if employee_on_leave(
            employee.id,
            work_date
        ):
            continue

        if employee_has_schedule(
            employee.id,
            work_date,
            shift
        ):
            continue

        workload = get_employee_workload(
            employee.id,
            work_date
        )

        available.append(
            (
                employee,
                workload
            )
        )

    available.sort(
        key=lambda item: (
            item[1],
            item[0].full_name.lower(),
        )
    )

    return [
        employee
        for employee, workload
        in available
    ]


# =========================================================
# LẤY DANH SÁCH CÔNG VIỆC
# =========================================================

def get_tasks():

    tasks = Task.query.all()

    tasks.sort(
        key=lambda task: (
            PRIORITY_ORDER.get(
                task.priority,
                99
            ),
            task.task_name.lower(),
        )
    )

    return tasks


# =========================================================
# ĐẾM SỐ LẦN TASK ĐÃ ĐƯỢC GIAO TRONG NGÀY
# =========================================================

def get_task_daily_load(
    task_id,
    work_date
):

    return (
        Schedule.query
        .filter(
            Schedule.task_id == task_id,
            Schedule.work_date == work_date,
        )
        .count()
    )


# =========================================================
# CHỌN TASK PHÙ HỢP
# =========================================================

def choose_task(
    employee,
    tasks,
    work_date
):

    if not tasks:
        return None

    employee_department = (
        employee.department
        or ""
    ).strip().lower()

    # -----------------------------------------------------
    # ƯU TIÊN TASK TRÙNG PHÒNG BAN
    # -----------------------------------------------------

    matching_tasks = [
        task
        for task in tasks
        if (
            task.category
            and task.category.strip().lower()
            == employee_department
        )
    ]

    candidate_tasks = (
        matching_tasks
        if matching_tasks
        else tasks
    )

    # -----------------------------------------------------
    # TASK ÍT ĐƯỢC PHÂN CÔNG NHẤT
    # -----------------------------------------------------

    candidate_tasks = sorted(
        candidate_tasks,
        key=lambda task: (
            get_task_daily_load(
                task.id,
                work_date
            ),
            PRIORITY_ORDER.get(
                task.priority,
                99
            ),
            task.task_name.lower(),
        )
    )

    return candidate_tasks[0]


# =========================================================
# PHÂN CÔNG TỰ ĐỘNG
# =========================================================

def auto_assign(
    work_date,
    shift,
    limit=5
):

    # -----------------------------------------------------
    # HỖ TRỢ NẾU ROUTE TRUYỀN DATE DẠNG CHUỖI
    # -----------------------------------------------------

    if isinstance(
        work_date,
        str
    ):

        work_date = date.fromisoformat(
            work_date
        )

    # -----------------------------------------------------
    # KIỂM TRA LIMIT
    # -----------------------------------------------------

    try:
        limit = int(limit)

    except (
        TypeError,
        ValueError
    ):
        limit = 5

    if limit < 1:
        limit = 1

    # -----------------------------------------------------
    # KIỂM TRA CA
    # -----------------------------------------------------

    if shift not in {
        "Sáng",
        "Chiều"
    }:
        shift = "Sáng"

    # -----------------------------------------------------
    # NHÂN VIÊN KHẢ DỤNG
    # -----------------------------------------------------

    employees = get_available_employees(
        work_date,
        shift
    )

    # -----------------------------------------------------
    # TASK
    # -----------------------------------------------------

    tasks = get_tasks()

    if not employees or not tasks:
        return []

    selected_employees = (
        employees[:limit]
    )

    assigned = []

    # -----------------------------------------------------
    # TẠO LỊCH
    # -----------------------------------------------------

    try:

        for employee in selected_employees:

            task = choose_task(
                employee,
                tasks,
                work_date
            )

            if task is None:
                continue

            schedule = Schedule(
                employee_id=employee.id,
                task_id=task.id,
                work_date=work_date,
                shift=shift,
                status="Đã phân công",
                note="Phân công tự động",
            )

            db.session.add(
                schedule
            )

            # flush để lần chọn tiếp theo
            # thấy được dữ liệu vừa thêm
            db.session.flush()

            assigned.append(
                (
                    employee.full_name,
                    task.task_name,
                )
            )

        db.session.commit()

    except Exception:

        db.session.rollback()
        raise

    return assigned
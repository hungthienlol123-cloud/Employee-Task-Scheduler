from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from flask_login import login_required

from app import db
from app.models import ActivityLog, Task
from app.routes import admin_required


# =========================================================
# BLUEPRINT
# =========================================================

task_bp = Blueprint(
    "task",
    __name__,
    url_prefix="/tasks",
)


# =========================================================
# KIỂM TRA GIỜ DỰ KIẾN
# =========================================================

def get_estimated_hours(value):

    try:
        hours = float(value)

        if hours <= 0:
            raise ValueError

        return hours

    except (TypeError, ValueError):
        return None


# =========================================================
# DANH SÁCH CÔNG VIỆC
# =========================================================

@task_bp.route("/")
@login_required
@admin_required
def index():

    q = request.args.get(
        "q",
        ""
    ).strip()

    priority = request.args.get(
        "priority",
        ""
    ).strip()

    query = Task.query

    if q:

        keyword = f"%{q}%"

        query = query.filter(
            db.or_(
                Task.task_name.ilike(keyword),
                Task.category.ilike(keyword),
                Task.description.ilike(keyword),
            )
        )

    if priority:

        query = query.filter(
            Task.priority == priority
        )

    tasks = (
        query
        .order_by(
            Task.id.desc()
        )
        .all()
    )

    return render_template(
        "task/list.html",
        tasks=tasks,
    )


# =========================================================
# THÊM CÔNG VIỆC
# =========================================================

@task_bp.route(
    "/new",
    methods=["GET", "POST"],
)
@login_required
@admin_required
def create():

    if request.method == "POST":

        task_name = request.form.get(
            "task_name",
            ""
        ).strip()

        category = request.form.get(
            "category",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        priority = request.form.get(
            "priority",
            "Trung bình"
        ).strip()

        estimated_hours = get_estimated_hours(
            request.form.get(
                "estimated_hours"
            )
        )

        if not task_name:

            flash(
                "Vui lòng nhập tên công việc.",
                "warning",
            )

            return redirect(
                url_for("task.create")
            )

        if priority not in {
            "Cao",
            "Trung bình",
            "Thấp",
        }:
            priority = "Trung bình"

        if estimated_hours is None:

            flash(
                "Số giờ dự kiến phải lớn hơn 0.",
                "warning",
            )

            return redirect(
                url_for("task.create")
            )

        task = Task(
            task_name=task_name,
            category=category or None,
            description=description or None,
            priority=priority,
            estimated_hours=estimated_hours,
        )

        db.session.add(task)

        db.session.add(
            ActivityLog(
                action=(
                    "Thêm công việc: "
                    f"{task_name}"
                )
            )
        )

        db.session.commit()

        flash(
            "Đã tạo công việc mới.",
            "success",
        )

        return redirect(
            url_for("task.index")
        )

    return render_template(
        "task/form.html",
        task=None,
    )


# =========================================================
# CHỈNH SỬA CÔNG VIỆC
# =========================================================

@task_bp.route(
    "/<int:task_id>/edit",
    methods=["GET", "POST"],
)
@login_required
@admin_required
def edit(task_id):

    task = db.session.get(
        Task,
        task_id,
    )

    if task is None:

        flash(
            "Không tìm thấy công việc.",
            "warning",
        )

        return redirect(
            url_for("task.index")
        )

    if request.method == "POST":

        task_name = request.form.get(
            "task_name",
            ""
        ).strip()

        category = request.form.get(
            "category",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        priority = request.form.get(
            "priority",
            "Trung bình"
        ).strip()

        estimated_hours = get_estimated_hours(
            request.form.get(
                "estimated_hours"
            )
        )

        if not task_name:

            flash(
                "Tên công việc không được để trống.",
                "warning",
            )

            return redirect(
                url_for(
                    "task.edit",
                    task_id=task.id,
                )
            )

        if priority not in {
            "Cao",
            "Trung bình",
            "Thấp",
        }:
            priority = "Trung bình"

        if estimated_hours is None:

            flash(
                "Số giờ dự kiến phải lớn hơn 0.",
                "warning",
            )

            return redirect(
                url_for(
                    "task.edit",
                    task_id=task.id,
                )
            )

        task.task_name = task_name
        task.category = category or None
        task.description = description or None
        task.priority = priority
        task.estimated_hours = estimated_hours

        db.session.add(
            ActivityLog(
                action=(
                    "Cập nhật công việc: "
                    f"{task_name}"
                )
            )
        )

        db.session.commit()

        flash(
            "Đã cập nhật công việc.",
            "success",
        )

        return redirect(
            url_for("task.index")
        )

    return render_template(
        "task/form.html",
        task=task,
    )


# =========================================================
# XÓA CÔNG VIỆC
# =========================================================

@task_bp.post(
    "/<int:task_id>/delete"
)
@login_required
@admin_required
def delete(task_id):

    task = db.session.get(
        Task,
        task_id,
    )

    if task is None:

        flash(
            "Không tìm thấy công việc.",
            "warning",
        )

        return redirect(
            url_for("task.index")
        )

    task_name = task.task_name

    db.session.delete(task)

    db.session.add(
        ActivityLog(
            action=(
                "Xóa công việc: "
                f"{task_name}"
            )
        )
    )

    db.session.commit()

    flash(
        "Đã xóa công việc.",
        "success",
    )

    return redirect(
        url_for("task.index")
    )
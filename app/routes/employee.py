from datetime import date, datetime
from pathlib import Path

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from flask_login import login_required
from werkzeug.utils import secure_filename

from app import db
from app.models import (
    ActivityLog,
    Employee,
    EmployeeRegistrationRequest,
    User,
)

from app.routes import admin_required
from app.services import (
    import_records,
    read_csv_file,
    read_google_sheet,
    read_xlsx_file,
)


employee_bp = Blueprint(
    "employee",
    __name__,
    url_prefix="/employees",
)


# =========================================================
# KIỂM TRA ẢNH
# =========================================================

def allowed_image(filename):

    if "." not in filename:
        return False

    extension = (
        filename
        .rsplit(".", 1)[1]
        .lower()
    )

    allowed_extensions = (
        current_app.config.get(
            "ALLOWED_IMAGE_EXTENSIONS",
            {
                "png",
                "jpg",
                "jpeg",
                "gif",
                "bmp",
            },
        )
    )

    return extension in allowed_extensions


# =========================================================
# TẠO USERNAME KHÔNG TRÙNG
# =========================================================

def create_unique_username(
    full_name,
    email,
):

    if email and "@" in email:
        base = email.split("@")[0]
    else:
        base = (
            full_name
            .lower()
            .replace(" ", "")
        )

    base = "".join(
        character
        for character in base
        if (
            character.isalnum()
            or character in "._"
        )
    )

    if not base:
        base = "employee"

    base = base[:50]

    username = base
    counter = 1

    while (
        User.query
        .filter_by(username=username)
        .first()
        is not None
    ):
        username = (
            f"{base}{counter}"
        )

        counter += 1

    return username


# =========================================================
# DANH SÁCH NHÂN VIÊN
# =========================================================

@employee_bp.route("/")
@login_required
@admin_required
def index():

    query_text = (
        request.args
        .get("q", "")
        .strip()
    )

    department = (
        request.args
        .get("department", "")
        .strip()
    )

    query = Employee.query

    if query_text:

        search_value = (
            f"%{query_text}%"
        )

        query = query.filter(
            db.or_(
                Employee.full_name.ilike(
                    search_value
                ),
                Employee.email.ilike(
                    search_value
                ),
                Employee.phone.ilike(
                    search_value
                ),
                Employee.position.ilike(
                    search_value
                ),
            )
        )

    if department:

        query = query.filter(
            Employee.department
            == department
        )

    employees = (
        query
        .order_by(
            Employee.id.desc()
        )
        .all()
    )

    departments = [
        row[0]
        for row in (
            db.session.query(
                Employee.department
            )
            .filter(
                Employee.department
                .isnot(None)
            )
            .distinct()
            .order_by(
                Employee.department.asc()
            )
            .all()
        )
        if row[0]
    ]

    return render_template(
        "employee/list.html",
        employees=employees,
        departments=departments,
    )


# =========================================================
# THÊM NHÂN VIÊN
# =========================================================

@employee_bp.route(
    "/new",
    methods=["GET", "POST"],
)
@login_required
@admin_required
def create():

    if request.method == "POST":

        full_name = (
            request.form
            .get("full_name", "")
            .strip()
        )

        department = (
            request.form
            .get("department", "")
            .strip()
        )

        email = (
            request.form
            .get("email", "")
            .strip()
            .lower()
        )

        phone = (
            request.form
            .get("phone", "")
            .strip()
        )

        position = (
            request.form
            .get("position", "")
            .strip()
        )

        hire_date_text = (
            request.form
            .get("hire_date", "")
            .strip()
        )

        skills = (
            request.form
            .get("skills", "")
            .strip()
        )

        address = (
            request.form
            .get("address", "")
            .strip()
        )

        if (
            not full_name
            or not department
            or not email
        ):
            flash(
                "Vui lòng nhập họ tên, phòng ban và email.",
                "warning",
            )

            return redirect(
                url_for(
                    "employee.create"
                )
            )

        existing = (
            Employee.query
            .filter(
                db.func.lower(
                    Employee.email
                )
                == email
            )
            .first()
        )

        if existing:

            flash(
                "Email nhân viên đã tồn tại.",
                "danger",
            )

            return redirect(
                url_for(
                    "employee.create"
                )
            )

        hire_date = None

        if hire_date_text:

            try:
                hire_date = date.fromisoformat(
                    hire_date_text
                )

            except ValueError:

                flash(
                    "Ngày vào làm không hợp lệ.",
                    "warning",
                )

                return redirect(
                    url_for(
                        "employee.create"
                    )
                )

        employee = Employee(
            full_name=full_name,
            department=department,
            email=email,
            phone=phone or None,
            position=position or None,
            hire_date=hire_date,
            skills=skills or None,
            address=address or None,
            active=True,
        )

        db.session.add(employee)
        db.session.flush()

        # -------------------------------------------------
        # ẢNH NHÂN VIÊN
        # -------------------------------------------------

        photo = request.files.get(
            "photo"
        )

        if (
            photo
            and photo.filename
            and allowed_image(
                photo.filename
            )
        ):

            original_name = secure_filename(
                photo.filename
            )

            extension = (
                original_name
                .rsplit(".", 1)[1]
                .lower()
            )

            filename = (
                f"employee_{employee.id}_"
                f"{int(datetime.now().timestamp())}"
                f".{extension}"
            )

            upload_folder = Path(
                current_app.config[
                    "UPLOAD_FOLDER"
                ]
            )

            upload_folder.mkdir(
                parents=True,
                exist_ok=True,
            )

            photo.save(
                upload_folder / filename
            )

            employee.photo_path = (
                f"img/employees/{filename}"
            )

        # -------------------------------------------------
        # TẠO TÀI KHOẢN
        # -------------------------------------------------

        create_account = (
            request.form.get(
                "create_account"
            )
            is not None
        )

        created_username = None

        if create_account:

            created_username = (
                create_unique_username(
                    full_name,
                    email,
                )
            )

            user = User(
                username=created_username,
                full_name=full_name,
                role="employee",
                employee_id=employee.id,
            )

            user.set_password(
                "123456"
            )

            db.session.add(user)

        db.session.add(
            ActivityLog(
                action=(
                    "Thêm nhân viên: "
                    f"{full_name}"
                )
            )
        )

        db.session.commit()

        if created_username:

            flash(
                (
                    "Đã thêm nhân viên. "
                    f"Tài khoản: {created_username} / "
                    "Mật khẩu: 123456"
                ),
                "success",
            )

        else:

            flash(
                "Đã thêm nhân viên.",
                "success",
            )

        return redirect(
            url_for(
                "employee.index"
            )
        )

    return render_template(
        "employee/form.html",
        employee=None,
    )


# =========================================================
# HỒ SƠ NHÂN VIÊN
# =========================================================

@employee_bp.route(
    "/<int:employee_id>"
)
@login_required
@admin_required
def profile(employee_id):

    employee = db.session.get(
        Employee,
        employee_id,
    )

    if employee is None:

        flash(
            "Không tìm thấy nhân viên.",
            "warning",
        )

        return redirect(
            url_for(
                "employee.index"
            )
        )

    return render_template(
        "employee/profile.html",
        employee=employee,
    )


# =========================================================
# CHỈNH SỬA NHÂN VIÊN
# =========================================================

@employee_bp.route(
    "/<int:employee_id>/edit",
    methods=["GET", "POST"],
)
@login_required
@admin_required
def edit(employee_id):

    employee = db.session.get(
        Employee,
        employee_id,
    )

    if employee is None:

        flash(
            "Không tìm thấy nhân viên.",
            "warning",
        )

        return redirect(
            url_for(
                "employee.index"
            )
        )

    if request.method == "POST":

        full_name = (
            request.form
            .get("full_name", "")
            .strip()
        )

        department = (
            request.form
            .get("department", "")
            .strip()
        )

        email = (
            request.form
            .get("email", "")
            .strip()
            .lower()
        )

        phone = (
            request.form
            .get("phone", "")
            .strip()
        )

        position = (
            request.form
            .get("position", "")
            .strip()
        )

        hire_date_text = (
            request.form
            .get("hire_date", "")
            .strip()
        )

        skills = (
            request.form
            .get("skills", "")
            .strip()
        )

        address = (
            request.form
            .get("address", "")
            .strip()
        )

        if (
            not full_name
            or not department
            or not email
        ):

            flash(
                "Vui lòng nhập đầy đủ thông tin bắt buộc.",
                "warning",
            )

            return redirect(
                url_for(
                    "employee.edit",
                    employee_id=employee.id,
                )
            )

        duplicate = (
            Employee.query
            .filter(
                db.func.lower(
                    Employee.email
                )
                == email,
                Employee.id
                != employee.id,
            )
            .first()
        )

        if duplicate:

            flash(
                "Email này đang thuộc nhân viên khác.",
                "danger",
            )

            return redirect(
                url_for(
                    "employee.edit",
                    employee_id=employee.id,
                )
            )

        hire_date = None

        if hire_date_text:

            try:

                hire_date = date.fromisoformat(
                    hire_date_text
                )

            except ValueError:

                flash(
                    "Ngày vào làm không hợp lệ.",
                    "warning",
                )

                return redirect(
                    url_for(
                        "employee.edit",
                        employee_id=employee.id,
                    )
                )

        employee.full_name = full_name
        employee.department = department
        employee.email = email
        employee.phone = phone or None
        employee.position = position or None
        employee.hire_date = hire_date
        employee.skills = skills or None
        employee.address = address or None

        # -------------------------------------------------
        # ẢNH MỚI
        # -------------------------------------------------

        photo = request.files.get(
            "photo"
        )

        if photo and photo.filename:

            if not allowed_image(
                photo.filename
            ):

                flash(
                    "Định dạng ảnh không hợp lệ.",
                    "warning",
                )

                return redirect(
                    url_for(
                        "employee.edit",
                        employee_id=employee.id,
                    )
                )

            original_name = secure_filename(
                photo.filename
            )

            extension = (
                original_name
                .rsplit(".", 1)[1]
                .lower()
            )

            filename = (
                f"employee_{employee.id}_"
                f"{int(datetime.now().timestamp())}"
                f".{extension}"
            )

            upload_folder = Path(
                current_app.config[
                    "UPLOAD_FOLDER"
                ]
            )

            upload_folder.mkdir(
                parents=True,
                exist_ok=True,
            )

            photo.save(
                upload_folder / filename
            )

            employee.photo_path = (
                f"img/employees/{filename}"
            )

        # -------------------------------------------------
        # UPDATE TÊN USER
        # -------------------------------------------------

        if employee.user:

            employee.user.full_name = (
                full_name
            )

        db.session.add(
            ActivityLog(
                action=(
                    "Cập nhật nhân viên: "
                    f"{full_name}"
                )
            )
        )

        db.session.commit()

        flash(
            "Đã cập nhật nhân viên.",
            "success",
        )

        return redirect(
            url_for(
                "employee.profile",
                employee_id=employee.id,
            )
        )

    return render_template(
        "employee/form.html",
        employee=employee,
    )


# =========================================================
# BẬT / TẮT NHÂN VIÊN
# =========================================================

@employee_bp.post(
    "/<int:employee_id>/toggle"
)
@login_required
@admin_required
def toggle(employee_id):

    employee = db.session.get(
        Employee,
        employee_id,
    )

    if employee is None:

        flash(
            "Không tìm thấy nhân viên.",
            "warning",
        )

        return redirect(
            url_for(
                "employee.index"
            )
        )

    employee.active = not employee.active

    db.session.commit()

    flash(
        "Đã cập nhật trạng thái nhân viên.",
        "success",
    )

    return redirect(
        url_for(
            "employee.index"
        )
    )


# =========================================================
# XÓA NHÂN VIÊN
# =========================================================

@employee_bp.post(
    "/<int:employee_id>/delete"
)
@login_required
@admin_required
def delete(employee_id):

    employee = db.session.get(
        Employee,
        employee_id,
    )

    if employee is None:

        flash(
            "Không tìm thấy nhân viên.",
            "warning",
        )

        return redirect(
            url_for(
                "employee.index"
            )
        )

    employee_name = (
        employee.full_name
    )

    if employee.user:

        db.session.delete(
            employee.user
        )

        db.session.flush()

    db.session.delete(
        employee
    )

    db.session.add(
        ActivityLog(
            action=(
                "Xóa nhân viên: "
                f"{employee_name}"
            )
        )
    )

    db.session.commit()

    flash(
        "Đã xóa nhân viên.",
        "success",
    )

    return redirect(
        url_for(
            "employee.index"
        )
    )


# =========================================================
# IMPORT EXCEL / CSV / GOOGLE SHEETS
# =========================================================

@employee_bp.route(
    "/import",
    methods=["GET", "POST"],
)
@login_required
@admin_required
def import_data():

    result = None

    if request.method == "POST":

        create_accounts = (
            request.form.get(
                "create_accounts"
            )
            is not None
        )

        # -------------------------------------------------
        # GOOGLE SHEETS
        # -------------------------------------------------

        google_url = (
            request.form
            .get("google_url", "")
            .strip()
        )

        if not google_url:

            google_url = (
                request.form
                .get("sheet_url", "")
                .strip()
            )

        if google_url:

            try:

                records = read_google_sheet(
                    google_url
                )

                result = import_records(
                    records,
                    create_accounts=create_accounts,
                )

                flash(
                    "Nhập Google Sheets thành công.",
                    "success",
                )

            except Exception as exc:

                flash(
                    (
                        "Không thể đọc Google Sheets: "
                        f"{exc}"
                    ),
                    "danger",
                )

            return render_template(
                "employee/import.html",
                result=result,
            )

        # -------------------------------------------------
        # FILE
        # -------------------------------------------------

        uploaded_file = request.files.get(
            "file"
        )

        if (
            uploaded_file is None
            or not uploaded_file.filename
        ):

            flash(
                "Vui lòng chọn file CSV hoặc Excel.",
                "warning",
            )

            return render_template(
                "employee/import.html",
                result=result,
            )

        filename = secure_filename(
            uploaded_file.filename
        )

        extension = (
            filename
            .rsplit(".", 1)[-1]
            .lower()
        )

        if extension not in {
            "csv",
            "xlsx",
        }:

            flash(
                "Chỉ hỗ trợ file .csv hoặc .xlsx.",
                "warning",
            )

            return render_template(
                "employee/import.html",
                result=result,
            )

        temp_folder = (
            Path(
                current_app.instance_path
            )
            / "imports"
        )

        temp_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        temp_path = (
            temp_folder
            / (
                f"{int(datetime.now().timestamp())}_"
                f"{filename}"
            )
        )

        uploaded_file.save(
            temp_path
        )

        try:

            if extension == "csv":

                records = read_csv_file(
                    temp_path
                )

            else:

                records = read_xlsx_file(
                    temp_path
                )

            result = import_records(
                records,
                create_accounts=create_accounts,
            )

            flash(
                "Nhập dữ liệu thành công.",
                "success",
            )

        except Exception as exc:

            db.session.rollback()

            flash(
                (
                    "Không thể nhập dữ liệu: "
                    f"{exc}"
                ),
                "danger",
            )

        finally:

            try:

                if temp_path.exists():

                    temp_path.unlink()

            except OSError:
                pass

    return render_template(
        "employee/import.html",
        result=result,
    )


# =========================================================
# DANH SÁCH YÊU CẦU ĐĂNG KÝ
# =========================================================

@employee_bp.route(
    "/approvals"
)
@login_required
@admin_required
def approvals():

    items = (
        EmployeeRegistrationRequest.query
        .order_by(
            EmployeeRegistrationRequest
            .created_at
            .desc()
        )
        .all()
    )

    return render_template(
        "employee/approvals.html",
        items=items,
    )


# =========================================================
# DUYỆT TÀI KHOẢN
# =========================================================

@employee_bp.post(
    "/approvals/<int:request_id>/approve"
)
@login_required
@admin_required
def approve(request_id):

    registration = db.session.get(
        EmployeeRegistrationRequest,
        request_id,
    )

    if registration is None:

        flash(
            "Không tìm thấy yêu cầu đăng ký.",
            "warning",
        )

        return redirect(
            url_for(
                "employee.approvals"
            )
        )

    if registration.status != "Chờ duyệt":

        flash(
            "Yêu cầu này đã được xử lý.",
            "info",
        )

        return redirect(
            url_for(
                "employee.approvals"
            )
        )

    # -----------------------------------------------------
    # KIỂM TRA USERNAME
    # -----------------------------------------------------

    username_exists = (
        User.query
        .filter_by(
            username=registration.username
        )
        .first()
    )

    if username_exists:

        flash(
            "Username đã tồn tại.",
            "danger",
        )

        return redirect(
            url_for(
                "employee.approvals"
            )
        )

    # -----------------------------------------------------
    # TÌM HOẶC TẠO EMPLOYEE
    # -----------------------------------------------------

    employee = (
        Employee.query
        .filter(
            db.func.lower(
                Employee.email
            )
            == registration.email.lower()
        )
        .first()
    )

    if employee is None:

        employee = Employee(
            full_name=registration.full_name,
            department=(
                registration.department
                or "Chưa cập nhật"
            ),
            email=registration.email.lower(),
            phone=registration.phone,
            active=True,
        )

        db.session.add(
            employee
        )

        db.session.flush()

    elif employee.user:

        flash(
            "Nhân viên này đã có tài khoản.",
            "danger",
        )

        return redirect(
            url_for(
                "employee.approvals"
            )
        )

    # -----------------------------------------------------
    # TẠO USER TỪ PASSWORD_HASH ĐÃ ĐĂNG KÝ
    # -----------------------------------------------------

    user = User(
        username=registration.username,
        full_name=registration.full_name,
        role="employee",
        employee_id=employee.id,
    )

    user.password_hash = (
        registration.password_hash
    )

    db.session.add(
        user
    )

    registration.status = (
        "Đã duyệt"
    )

    registration.reviewed_at = (
        datetime.utcnow()
    )

    db.session.add(
        ActivityLog(
            action=(
                "Duyệt tài khoản nhân viên: "
                f"{registration.username}"
            )
        )
    )

    db.session.commit()

    flash(
        "Đã duyệt tài khoản nhân viên.",
        "success",
    )

    return redirect(
        url_for(
            "employee.approvals"
        )
    )


# =========================================================
# TỪ CHỐI TÀI KHOẢN
# =========================================================

@employee_bp.post(
    "/approvals/<int:request_id>/reject"
)
@login_required
@admin_required
def reject(request_id):

    registration = db.session.get(
        EmployeeRegistrationRequest,
        request_id,
    )

    if registration is None:

        flash(
            "Không tìm thấy yêu cầu đăng ký.",
            "warning",
        )

        return redirect(
            url_for(
                "employee.approvals"
            )
        )

    if registration.status != "Chờ duyệt":

        flash(
            "Yêu cầu này đã được xử lý.",
            "info",
        )

        return redirect(
            url_for(
                "employee.approvals"
            )
        )

    registration.status = (
        "Từ chối"
    )

    registration.reviewed_at = (
        datetime.utcnow()
    )

    db.session.add(
        ActivityLog(
            action=(
                "Từ chối tài khoản: "
                f"{registration.username}"
            )
        )
    )

    db.session.commit()

    flash(
        "Đã từ chối yêu cầu đăng ký.",
        "success",
    )

    return redirect(
        url_for(
            "employee.approvals"
        )
    )
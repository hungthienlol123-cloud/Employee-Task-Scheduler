from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for
)

from flask_login import (
    current_user,
    login_user,
    logout_user
)

from app import db

from app.models import (
    ActivityLog,
    EmployeeRegistrationRequest,
    User
)


# =========================================================
# BLUEPRINT
# =========================================================

auth_bp = Blueprint(
    "auth",
    __name__
)


# =========================================================
# TRANG CHỦ
# =========================================================

@auth_bp.route("/")
def landing():

    if current_user.is_authenticated:

        return redirect(
            url_for("dashboard.home")
        )

    return render_template(
        "landing.html"
    )


# =========================================================
# ĐĂNG NHẬP
# =========================================================

@auth_bp.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if current_user.is_authenticated:

        return redirect(
            url_for("dashboard.home")
        )

    if request.method == "POST":

        username = (
            request.form
            .get("username", "")
            .strip()
        )

        password = (
            request.form
            .get("password", "")
        )

        role = (
            request.form
            .get("role", "employee")
        )

        admin_code = (
            request.form
            .get("admin_code", "")
            .strip()
        )

        user = (
            User.query
            .filter_by(
                username=username
            )
            .first()
        )

        # -------------------------------------------------
        # USERNAME / PASSWORD
        # -------------------------------------------------

        if (
            not user
            or
            not user.check_password(password)
        ):

            flash(
                "Sai tên đăng nhập hoặc mật khẩu.",
                "danger"
            )

            return redirect(
                url_for("auth.login")
            )

        # -------------------------------------------------
        # ROLE
        # -------------------------------------------------

        if user.role != role:

            flash(
                "Tài khoản không thuộc vai trò đã chọn.",
                "danger"
            )

            return redirect(
                url_for("auth.login")
            )

        # -------------------------------------------------
        # ADMIN CODE
        # -------------------------------------------------

        if role == "admin":

            if admin_code != (
                user.admin_code or ""
            ):

                flash(
                    "Mã đăng nhập Admin không chính xác.",
                    "danger"
                )

                return redirect(
                    url_for("auth.login")
                )

        # -------------------------------------------------
        # LOGIN
        # -------------------------------------------------

        login_user(user)

        db.session.add(
            ActivityLog(
                user_id=user.id,
                action=(
                    "Đăng nhập hệ thống "
                    f"với vai trò {role}"
                )
            )
        )

        db.session.commit()

        return redirect(
            url_for("dashboard.home")
        )

    return render_template(
        "auth/login.html"
    )


# =========================================================
# ĐĂNG KÝ NHÂN VIÊN
# =========================================================

@auth_bp.post("/register")
def register_employee():

    full_name = (
        request.form
        .get("full_name", "")
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

    department = (
        request.form
        .get("department", "")
        .strip()
    )

    username = (
        request.form
        .get("register_username", "")
        .strip()
    )

    password = (
        request.form
        .get("register_password", "")
    )

    confirm = (
        request.form
        .get("confirm_password", "")
    )

    # -----------------------------------------------------
    # KIỂM TRA THÔNG TIN
    # -----------------------------------------------------

    if (
        not full_name
        or
        not email
        or
        not username
        or
        not password
    ):

        flash(
            "Vui lòng nhập đầy đủ thông tin bắt buộc.",
            "warning"
        )

        return redirect(
            url_for("auth.login")
            + "#register"
        )

    # -----------------------------------------------------
    # PASSWORD
    # -----------------------------------------------------

    if len(password) < 6:

        flash(
            "Mật khẩu phải có ít nhất 6 ký tự.",
            "warning"
        )

        return redirect(
            url_for("auth.login")
            + "#register"
        )

    if password != confirm:

        flash(
            "Hai mật khẩu không khớp.",
            "warning"
        )

        return redirect(
            url_for("auth.login")
            + "#register"
        )

    # -----------------------------------------------------
    # USERNAME ĐÃ TỒN TẠI
    # -----------------------------------------------------

    existing_user = (
        User.query
        .filter_by(
            username=username
        )
        .first()
    )

    if existing_user:

        flash(
            "Tên đăng nhập đã tồn tại.",
            "danger"
        )

        return redirect(
            url_for("auth.login")
            + "#register"
        )

    # -----------------------------------------------------
    # YÊU CẦU ĐANG CHỜ
    # -----------------------------------------------------

    pending = (
        EmployeeRegistrationRequest
        .query
        .filter(
            EmployeeRegistrationRequest.status
            == "Chờ duyệt",

            db.or_(
                db.func.lower(
                    EmployeeRegistrationRequest.email
                )
                == email,

                EmployeeRegistrationRequest.username
                == username
            )
        )
        .first()
    )

    if pending:

        flash(
            "Yêu cầu đã được gửi và đang chờ Admin duyệt.",
            "info"
        )

        return redirect(
            url_for("auth.login")
            + "#register"
        )

    # -----------------------------------------------------
    # TẠO YÊU CẦU
    # -----------------------------------------------------

    registration = (
        EmployeeRegistrationRequest(
            full_name=full_name,
            email=email,
            phone=phone,
            department=(
                department
                or "Chưa cập nhật"
            ),
            username=username,
            status="Chờ duyệt"
        )
    )

    registration.set_password(
        password
    )

    db.session.add(
        registration
    )

    db.session.commit()

    flash(
        "Đã gửi yêu cầu đăng ký. "
        "Vui lòng chờ Admin duyệt.",
        "success"
    )

    return redirect(
        url_for("auth.login")
    )


# =========================================================
# ĐĂNG XUẤT
# =========================================================

@auth_bp.route("/logout")
def logout():

    if current_user.is_authenticated:

        db.session.add(
            ActivityLog(
                user_id=current_user.id,
                action="Đăng xuất hệ thống"
            )
        )

        db.session.commit()

    logout_user()

    return redirect(
        url_for("auth.landing")
    )
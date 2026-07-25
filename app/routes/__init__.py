from functools import wraps

from flask import abort
from flask_login import current_user


# =========================================================
# CHỈ ADMIN
# =========================================================

def admin_required(function):

    @wraps(function)
    def decorated_function(*args, **kwargs):

        if (
            not current_user.is_authenticated
            or current_user.role != "admin"
        ):
            abort(403)

        return function(*args, **kwargs)

    return decorated_function


# =========================================================
# CHỈ NHÂN VIÊN
# =========================================================

def employee_required(function):

    @wraps(function)
    def decorated_function(*args, **kwargs):

        if (
            not current_user.is_authenticated
            or current_user.role != "employee"
        ):
            abort(403)

        return function(*args, **kwargs)

    return decorated_function
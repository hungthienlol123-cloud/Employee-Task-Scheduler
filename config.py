from pathlib import Path


# =========================================================
# ĐƯỜNG DẪN PROJECT
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

INSTANCE_DIR = BASE_DIR / "instance"

DATABASE_FILE = INSTANCE_DIR / "database.db"

UPLOAD_FOLDER = (
    BASE_DIR
    / "app"
    / "static"
    / "img"
    / "employees"
)

BACKUP_FOLDER = (
    INSTANCE_DIR
    / "backups"
)


# =========================================================
# CONFIG
# =========================================================

class Config:

    SECRET_KEY = "workflow-vip-secret-key"

    SQLALCHEMY_DATABASE_URI = (
        f"sqlite:///{DATABASE_FILE.as_posix()}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAX_CONTENT_LENGTH = (
        5 * 1024 * 1024
    )

    UPLOAD_FOLDER = str(
        UPLOAD_FOLDER
    )

    BACKUP_FOLDER = str(
        BACKUP_FOLDER
    )

    ALLOWED_IMAGE_EXTENSIONS = {
        "png",
        "jpg",
        "jpeg",
        "gif",
        "bmp"
    }

    ADMIN_DEFAULT_CODE = "ADM-0001"
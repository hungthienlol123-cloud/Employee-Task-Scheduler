import sqlite3

from datetime import datetime
from pathlib import Path

from flask import current_app


def backup_database():

    # =====================================================
    # LẤY DATABASE URI
    # =====================================================

    database_uri = current_app.config[
        "SQLALCHEMY_DATABASE_URI"
    ]

    prefix = "sqlite:///"

    if not database_uri.startswith(prefix):

        raise RuntimeError(
            "Backup hiện chỉ hỗ trợ SQLite."
        )

    database_path = database_uri[
        len(prefix):
    ]

    source_path = Path(
        database_path
    )

    # =====================================================
    # KIỂM TRA DATABASE
    # =====================================================

    if not source_path.exists():

        raise FileNotFoundError(
            f"Không tìm thấy database: "
            f"{source_path}"
        )

    # =====================================================
    # THƯ MỤC BACKUP
    # =====================================================

    backup_folder = Path(
        current_app.config[
            "BACKUP_FOLDER"
        ]
    )

    backup_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    # =====================================================
    # TÊN FILE
    # =====================================================

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup_path = (
        backup_folder
        /
        f"workflow_backup_{timestamp}.db"
    )

    # =====================================================
    # SQLITE BACKUP API
    # =====================================================

    source_connection = None

    destination_connection = None

    try:

        source_connection = (
            sqlite3.connect(
                str(source_path)
            )
        )

        destination_connection = (
            sqlite3.connect(
                str(backup_path)
            )
        )

        source_connection.backup(
            destination_connection
        )

    finally:

        if destination_connection:

            destination_connection.close()

        if source_connection:

            source_connection.close()

    return str(
        backup_path
    )
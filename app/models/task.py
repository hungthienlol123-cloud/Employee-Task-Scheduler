from app import db


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)

    task_name = db.Column(
        db.String(150),
        nullable=False
    )

    category = db.Column(
        db.String(100),
        nullable=True
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    priority = db.Column(
        db.String(30),
        nullable=False,
        default="Trung bình"
    )

    estimated_hours = db.Column(
        db.Float,
        nullable=False,
        default=4.0
    )

    schedules = db.relationship(
        "Schedule",
        back_populates="task",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Task {self.id} - {self.task_name}>"
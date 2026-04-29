from app import db
from app.models import Task


def test_task_default_status(app):
    with app.app_context():
        task = Task(title="Ma tâche")
        db.session.add(task)
        db.session.commit()
        assert task.status == "todo"


def test_task_to_dict_keys(app):
    with app.app_context():
        task = Task(title="Test", description="desc", status="in_progress")
        db.session.add(task)
        db.session.commit()
        d = task.to_dict()
        assert d["title"] == "Test"
        assert d["status"] == "in_progress"
        assert "created_at" in d
        assert "updated_at" in d


def test_task_valid_statuses():
    assert "todo" in Task.VALID_STATUSES
    assert "in_progress" in Task.VALID_STATUSES
    assert "done" in Task.VALID_STATUSES
    assert "invalid" not in Task.VALID_STATUSES


def test_task_description_default(app):
    with app.app_context():
        task = Task(title="Sans description")
        db.session.add(task)
        db.session.commit()
        assert task.description == ""

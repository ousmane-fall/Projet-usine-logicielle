import logging

from flask import Blueprint, jsonify, render_template, request

from app import db
from app.models import Task

api_bp = Blueprint("api", __name__, template_folder="../templates")


@api_bp.route("/")
def index():
    return render_template("index.html")
logger = logging.getLogger(__name__)


@api_bp.route("/health")
def health():
    return jsonify({"status": "ok"})


@api_bp.route("/tasks", methods=["GET"])
def get_tasks():
    status = request.args.get("status")
    query = Task.query
    if status:
        query = query.filter_by(status=status)
    tasks = query.all()
    logger.info("Listed %d tasks", len(tasks))
    return jsonify([t.to_dict() for t in tasks])


@api_bp.route("/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    task = Task.query.get_or_404(task_id)
    return jsonify(task.to_dict())


@api_bp.route("/tasks", methods=["POST"])
def create_task():
    data = request.get_json()
    if not data or not data.get("title"):
        return jsonify({"error": "title is required"}), 400
    task = Task(
        title=data["title"],
        description=data.get("description", ""),
        status=data.get("status", "todo"),
    )
    if task.status not in Task.VALID_STATUSES:
        return jsonify({"error": "invalid status"}), 400
    db.session.add(task)
    db.session.commit()
    logger.info("Created task id=%d", task.id)
    return jsonify(task.to_dict()), 201


@api_bp.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    task = Task.query.get_or_404(task_id)
    data = request.get_json()
    if "title" in data:
        task.title = data["title"]
    if "description" in data:
        task.description = data["description"]
    if "status" in data:
        if data["status"] not in Task.VALID_STATUSES:
            return jsonify({"error": "invalid status"}), 400
        task.status = data["status"]
    db.session.commit()
    logger.info("Updated task id=%d", task_id)
    return jsonify(task.to_dict())


@api_bp.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    logger.info("Deleted task id=%d", task_id)
    return "", 204

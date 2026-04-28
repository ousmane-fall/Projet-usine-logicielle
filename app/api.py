import logging

from flask import Blueprint, jsonify, request

from app import db
from app.calculator import Calculator, CalculatorError
from app.models import Task

api_bp = Blueprint("api", __name__, template_folder="../templates")
logger = logging.getLogger(__name__)


@api_bp.route("/health")
def health():
    return jsonify({"status": "ok"})


_CALC_OPS = {
    "add": (Calculator.add, 2),
    "subtract": (Calculator.subtract, 2),
    "multiply": (Calculator.multiply, 2),
    "divide": (Calculator.divide, 2),
    "power": (Calculator.power, 2),
    "modulo": (Calculator.modulo, 2),
    "sqrt": (Calculator.sqrt, 1),
}


@api_bp.route("/calculate", methods=["POST"])
def calculate():
    """Calcule une expression ou applique une opération nommée.

    Corps JSON accepté :
      - {"expression": "1 + 2 * 3"}
      - {"operation": "add", "a": 1, "b": 2}
      - {"operation": "sqrt", "a": 9}
    """
    data = request.get_json(silent=True) or {}

    try:
        if "expression" in data:
            result = Calculator.calculate(data["expression"])
        elif "operation" in data:
            op_name = data["operation"]
            if op_name not in _CALC_OPS:
                return jsonify({"error": "operation inconnue"}), 400
            func, arity = _CALC_OPS[op_name]
            try:
                a = float(data["a"])
                args = [a] if arity == 1 else [a, float(data["b"])]
            except (KeyError, TypeError, ValueError):
                return jsonify({"error": "operandes invalides"}), 400
            result = func(*args)
        else:
            return jsonify({"error": "expression ou operation requise"}), 400
    except CalculatorError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify({"result": result})


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

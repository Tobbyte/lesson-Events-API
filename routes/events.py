from datetime import datetime  # noqa: D100

from flask import (  # pyright: ignore[reportMissingImports]
    Blueprint,
    jsonify,
    request,
)
from flask_jwt_extended import (  # pyright: ignore[reportMissingImports]
    get_jwt_identity,
    jwt_required,
)

from models import Event, User, db  # noqa: F401

events_bp = Blueprint("events", __name__, url_prefix="/api/events")


@events_bp.route("", methods=["GET"])
def get_events():  # noqa: ANN201
    """Get all events that the user can see"""  # noqa: D400, D415
    events = Event.query.all()
    return jsonify([event.to_dict() for event in events]), 200


@events_bp.route("/<int:event_id>", methods=["GET"])
def get_event(event_id):  # noqa: ANN001, ANN201
    """Get a specific event"""  # noqa: D400, D415
    event = Event.query.get_or_404(event_id)
    return jsonify(event.to_dict()), 200


@events_bp.route("", methods=["POST"])
@jwt_required()
def create_event():  # noqa: ANN201
    """Create a new event (requires authentication)"""  # noqa: D400, D415
    data = request.get_json()

    if not data or not data.get("title"):
        return jsonify({"error": "Title is required"}), 400

    if not data.get("date"):
        return jsonify({"error": "Date is required"}), 400

    # Parse date string to datetime
    try:
        event_date = datetime.fromisoformat(
            data["date"].replace("Z", "+00:00"),
        )
    except (ValueError, AttributeError):
        return jsonify({
            "error": "Invalid date format. Use ISO 8601 format (e.g., 2024-01-15T18:00:00)",  # noqa: E501
        }), 400

    user_id = int(get_jwt_identity())

    event = Event(
        title=data["title"],  # pyright: ignore[reportCallIssue]
        description=data.get("description"),  # pyright: ignore[reportCallIssue]
        date=event_date,  # pyright: ignore[reportCallIssue]
        location=data.get("location"),  # pyright: ignore[reportCallIssue]
        capacity=data.get("capacity"),  # None means unlimited # pyright: ignore[reportCallIssue]
        is_public=data.get("is_public", True),  # pyright: ignore[reportCallIssue]
        requires_admin=data.get("requires_admin", False),  # pyright: ignore[reportCallIssue]
        created_by=user_id,  # pyright: ignore[reportCallIssue]
    )

    db.session.add(event)
    db.session.commit()

    return jsonify(event.to_dict()), 201


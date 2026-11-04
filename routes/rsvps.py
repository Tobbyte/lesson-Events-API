from flask import (  # pyright: ignore[reportMissingImports] # noqa: D100
    Blueprint,
    jsonify,
    request,
)
from flask_jwt_extended import (  # pyright: ignore[reportMissingImports]
    get_jwt,
    get_jwt_identity,
    jwt_required,  # noqa: F401
    verify_jwt_in_request,
)
from flask_jwt_extended.exceptions import (  # pyright: ignore[reportMissingImports]
    NoAuthorizationError,
)

from models import RSVP, Event, User, db  # noqa: F401

rsvps_bp = Blueprint("rsvps", __name__, url_prefix="/api/rsvps")


def get_current_user():  # noqa: ANN201
    """Helper function to get current user if authenticated"""  # noqa: D400, D401, D415
    try:
        verify_jwt_in_request(optional=True)
        user_id_str = get_jwt_identity()
        if user_id_str:
            user_id = int(user_id_str)
            claims = get_jwt()
            return user_id, claims.get("is_admin", False)
        return None, False  # noqa: TRY300
    except (NoAuthorizationError, RuntimeError, ValueError):
        return None, False


@rsvps_bp.route("/event/<int:event_id>", methods=["POST"])
def rsvp(event_id):  # noqa: ANN001, ANN201
    """RSVP to an event with different access requirements"""  # noqa: D400, D415
    event = Event.query.get_or_404(event_id)
    data = request.get_json() or {}

    user_id, is_admin = get_current_user()

    # Check if event requires authentication
    if not event.is_public and user_id is None:
        return jsonify({
            "error": "Authentication required for this event",
        }), 401

    # Check if event requires admin
    if event.requires_admin:
        if user_id is None:
            return jsonify({
                "error": "Admin access required for this event",
            }), 401
        if not is_admin:
            return jsonify({
                "error": "Admin access required for this event",
            }), 403

    # Check capacity if set
    if event.capacity is not None:
        current_attendees = len([r for r in event.rsvps if r.attending])
        if current_attendees >= event.capacity:
            return jsonify({"error": "Event is at full capacity"}), 400

    # Check if user already RSVP'd
    existing_rsvp = None
    if user_id:
        existing_rsvp = RSVP.query.filter_by(
            event_id=event_id,
            user_id=user_id,
        ).first()

    # Default to attending=True if not specified
    attending = data.get("attending", True)

    if existing_rsvp:
        # Update existing RSVP
        existing_rsvp.attending = attending
        db.session.commit()
        return jsonify(existing_rsvp.to_dict()), 200
    # Create new RSVP
    rsvp = RSVP(
        event_id=event_id,  # pyright: ignore[reportCallIssue]
        user_id=user_id,  # pyright: ignore[reportCallIssue]
        attending=attending,  # pyright: ignore[reportCallIssue]
    )
    db.session.add(rsvp)
    db.session.commit()
    return jsonify(rsvp.to_dict()), 201


@rsvps_bp.route("/event/<int:event_id>", methods=["GET"])
def get_rsvps(event_id):  # noqa: ANN001, ANN201
    """Get all RSVPs for an event"""  # noqa: D400, D415
    event = Event.query.get_or_404(event_id)
    rsvps = RSVP.query.filter_by(event_id=event_id).all()

    attending_count = len([r for r in rsvps if r.attending])
    not_attending_count = len([r for r in rsvps if not r.attending])

    return jsonify({
        "event": event.to_dict(),
        "rsvps": [rsvp.to_dict() for rsvp in rsvps],
        "stats": {
            "attending": attending_count,
            "not_attending": not_attending_count,
            "total": len(rsvps),
        },
    }), 200


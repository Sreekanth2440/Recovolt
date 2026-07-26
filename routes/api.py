from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import db
from models.complaint import Complaint, Message
from models.notification import Notification

api = Blueprint("api", __name__, url_prefix="/api")

@api.route("/complaints/<int:complaint_id>/messages", methods=["GET"])
@login_required
def get_messages(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    
    # Check authorization
    if current_user.role == "consumer" and complaint.consumer_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403
    elif current_user.role == "worker" and complaint.assigned_worker_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403
        
    messages = Message.query.filter_by(complaint_id=complaint_id).order_by(Message.created_at.asc()).all()
    
    return jsonify({
        "messages": [
            {
                "id": m.id,
                "sender_id": m.sender_id,
                "sender_name": m.sender.name,
                "sender_role": m.sender.role,
                "content": m.content,
                "created_at": m.created_at.strftime("%I:%M %p")
            } for m in messages
        ]
    })

@api.route("/complaints/<int:complaint_id>/messages", methods=["POST"])
@login_required
def post_message(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    
    # Check authorization
    if current_user.role == "consumer" and complaint.consumer_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403
    elif current_user.role == "worker" and complaint.assigned_worker_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403
        
    data = request.get_json()
    if not data or not data.get("content"):
        return jsonify({"error": "Message content required"}), 400
        
    msg = Message(
        complaint_id=complaint_id,
        sender_id=current_user.id,
        content=data["content"].strip()
    )
    db.session.add(msg)
    
    # Send notification to the other party
    if current_user.role == "consumer" and complaint.assigned_worker_id:
        notif = Notification(
            user_id=complaint.assigned_worker_id,
            complaint_id=complaint_id,
            title=f"New Message on #{complaint_id}",
            message=f"{current_user.name} sent a message: {msg.content[:30]}..."
        )
        db.session.add(notif)
    elif current_user.role == "worker":
        notif = Notification(
            user_id=complaint.consumer_id,
            complaint_id=complaint_id,
            title=f"New Message on #{complaint_id}",
            message=f"Worker {current_user.name} sent a message: {msg.content[:30]}..."
        )
        db.session.add(notif)
        
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": {
            "id": msg.id,
            "sender_id": msg.sender_id,
            "sender_name": msg.sender.name,
            "sender_role": msg.sender.role,
            "content": msg.content,
            "created_at": msg.created_at.strftime("%I:%M %p")
        }
    })

from datetime import datetime, timezone
from models import db


class Complaint(db.Model):

    __tablename__ = "complaints"

    id = db.Column(db.Integer, primary_key=True)

    consumer_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )

    title = db.Column(db.String(200), nullable=False)

    description = db.Column(db.Text, nullable=False)

    category = db.Column(db.String(50), nullable=False)
    # Categories: power_outage, voltage_issue, meter_problem,
    #             billing, new_connection, other

    location = db.Column(db.String(255), nullable=False)

    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

    image = db.Column(db.String(255), nullable=True)

    status = db.Column(db.String(20), default="pending", nullable=False)
    # Status flow: pending -> assigned -> in_progress -> resolved -> closed

    priority = db.Column(db.String(10), default="medium", nullable=False)
    # Priority: low, medium, high

    assigned_worker_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True
    )

    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    resolved_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    consumer = db.relationship(
        "User", foreign_keys=[consumer_id], backref="complaints"
    )

    assigned_worker = db.relationship(
        "User", foreign_keys=[assigned_worker_id], backref="assigned_complaints"
    )

    feedback = db.relationship(
        "Feedback", backref="complaint", uselist=False, lazy=True
    )

    @property
    def status_display(self):
        """Human-readable status."""
        return self.status.replace("_", " ").title()

    @property
    def category_display(self):
        """Human-readable category."""
        return self.category.replace("_", " ").title()

    @property
    def priority_badge(self):
        """Bootstrap badge class for priority."""
        badges = {
            "low": "bg-info",
            "medium": "bg-warning text-dark",
            "high": "bg-danger",
        }
        return badges.get(self.priority, "bg-secondary")

    @property
    def status_badge(self):
        """Bootstrap badge class for status."""
        badges = {
            "pending": "bg-secondary",
            "assigned": "bg-info",
            "in_progress": "bg-warning text-dark",
            "resolved": "bg-success",
            "closed": "bg-dark",
        }
        return badges.get(self.status, "bg-secondary")


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    
    complaint_id = db.Column(
        db.Integer, db.ForeignKey("complaints.id"), nullable=False
    )
    
    sender_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )
    
    content = db.Column(db.Text, nullable=False)
    
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    complaint_ref = db.relationship(
        "Complaint", backref=db.backref("messages", lazy=True, order_by="Message.created_at.asc()")
    )
    
    sender = db.relationship("User", foreign_keys=[sender_id])

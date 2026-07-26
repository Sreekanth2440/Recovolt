from datetime import datetime, timezone
from models import db


class Feedback(db.Model):

    __tablename__ = "feedbacks"

    id = db.Column(db.Integer, primary_key=True)

    complaint_id = db.Column(
        db.Integer, db.ForeignKey("complaints.id"), unique=True, nullable=False
    )

    consumer_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )

    rating = db.Column(db.Integer, nullable=False)  # 1 to 5

    comment = db.Column(db.Text, nullable=True)

    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    consumer = db.relationship("User", backref="feedbacks")

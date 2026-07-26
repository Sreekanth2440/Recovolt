from models import db


class WorkerProfile(db.Model):

    __tablename__ = "worker_profiles"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False
    )

    section = db.Column(db.String(100), nullable=True)

    designation = db.Column(db.String(100), nullable=True)

    is_available = db.Column(db.Boolean, default=True)

    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

    # Relationship
    user = db.relationship("User", backref=db.backref("worker_profile", uselist=False))

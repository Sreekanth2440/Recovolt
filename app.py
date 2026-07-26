import os
from flask import Flask, render_template, request, flash, redirect
from flask_login import login_required, current_user
from sqlalchemy import func

from config import Config
from models import db, login_manager
from models.complaint import Complaint
from models.feedback import Feedback


def create_app():
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)

    # Ensure upload folder exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Register Blueprints
    from routes.auth import auth
    from routes.consumer import consumer
    from routes.worker import worker
    from routes.admin import admin
    from routes.api import api

    app.register_blueprint(auth)
    app.register_blueprint(consumer)
    app.register_blueprint(worker)
    app.register_blueprint(admin)
    app.register_blueprint(api)

    # ---------------- Home ---------------- #
    @app.route("/")
    def home():
        total = Complaint.query.count()
        resolved = Complaint.query.filter(
            Complaint.status.in_(["resolved", "closed"])
        ).count()

        avg_rating_result = db.session.query(func.avg(Feedback.rating)).scalar()
        avg_rating = round(float(avg_rating_result), 1) if avg_rating_result else 0.0

        resolution_rate = round((resolved / total) * 100) if total > 0 else 0

        testimonials = (
            Feedback.query.filter(
                Feedback.rating >= 4,
                Feedback.comment.isnot(None),
                Feedback.comment != "",
            )
            .order_by(Feedback.created_at.desc())
            .limit(6)
            .all()
        )

        return render_template(
            "index.html",
            stats={
                "total": total,
                "resolved": resolved,
                "avg_rating": avg_rating,
                "resolution_rate": resolution_rate,
            },
            testimonials=testimonials,
        )

    # ---------------- Public Complaint Tracker ---------------- #
    @app.route("/track", methods=["GET", "POST"])
    def track():
        complaint = None

        if request.method == "POST":
            complaint_id = request.form.get("complaint_id", "").strip()
            identifier = request.form.get("identifier", "").strip()

            if not complaint_id or not identifier:
                flash("Please enter both complaint ID and email or phone.", "warning")
            else:
                try:
                    cid = int(complaint_id)
                except ValueError:
                    flash("Invalid complaint ID.", "danger")
                else:
                    complaint = Complaint.query.get(cid)
                    if complaint and (
                        complaint.consumer.email.lower() == identifier.lower()
                        or complaint.consumer.phone == identifier
                    ):
                        pass
                    else:
                        complaint = None
                        flash(
                            "No complaint found matching those details. "
                            "Check your ID and registered email/phone.",
                            "danger",
                        )

        return render_template("track.html", complaint=complaint)

    # ---------------- About ---------------- #
    @app.route("/about")
    def about():
        return render_template("about.html")

    # ---------------- Contact ---------------- #
    @app.route("/contact")
    def contact():
        return render_template("contact.html")

    # ---------------- Mark Notifications Read ---------------- #
    @app.route("/notifications/mark-read")
    @login_required
    def mark_notifications_read():
        from models.notification import Notification
        Notification.query.filter_by(
            user_id=current_user.id, is_read=False
        ).update({"is_read": True})
        db.session.commit()
        flash("All notifications marked as read.", "success")
        return redirect(request.referrer or "/")

    # ---------------- Error Handlers ---------------- #
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    # ---------------- Global Notification & Section Context ---------------- #
    @app.context_processor
    def inject_global_vars():
        from flask_login import current_user
        from models.notification import Notification
        from utils.constants import ERNAKULAM_SECTIONS
        
        ctx = dict(ernakulam_sections=ERNAKULAM_SECTIONS)
        if current_user.is_authenticated:
            unread_count = Notification.query.filter_by(
                user_id=current_user.id, is_read=False
            ).count()
            recent_notifs = Notification.query.filter_by(
                user_id=current_user.id
            ).order_by(Notification.created_at.desc()).limit(5).all()
            ctx.update(
                unread_notifications_count=unread_count,
                recent_notifications=recent_notifs,
            )
        else:
            ctx.update(unread_notifications_count=0, recent_notifications=[])
        return ctx

    # Create database tables
    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
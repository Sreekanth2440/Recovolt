import os
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, current_app,
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import or_, case
from datetime import datetime, timezone

from models import db
from models.complaint import Complaint
from models.feedback import Feedback

consumer = Blueprint("consumer", __name__, url_prefix="/consumer")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def consumer_required(f):
    """Decorator to restrict access to consumers only."""
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.role != "consumer":
            flash("Access denied.", "danger")
            return redirect("/")
        return f(*args, **kwargs)

    return decorated


# ────────────────── Dashboard ────────────────── #

@consumer.route("/dashboard")
@login_required
@consumer_required
def dashboard():
    complaints = Complaint.query.filter_by(
        consumer_id=current_user.id
    ).order_by(Complaint.created_at.desc()).all()

    total = len(complaints)
    pending = sum(1 for c in complaints if c.status in ("pending", "assigned"))
    in_progress = sum(1 for c in complaints if c.status == "in_progress")
    resolved = sum(1 for c in complaints if c.status in ("resolved", "closed"))

    recent = complaints[:5]

    chart_data = {
        "labels": ["Pending", "In Progress", "Resolved"],
        "values": [pending, in_progress, resolved],
    }

    return render_template(
        "consumer/dashboard.html",
        total=total,
        pending=pending,
        in_progress=in_progress,
        resolved=resolved,
        recent=recent,
        chart_data=chart_data,
    )


# ────────────────── Profile ────────────────── #

@consumer.route("/profile", methods=["GET", "POST"])
@login_required
@consumer_required
def profile():
    if request.method == "POST":
        current_user.name = request.form.get("name", current_user.name)
        current_user.phone = request.form.get("phone", current_user.phone)
        current_user.address = request.form.get("address", current_user.address)
        current_user.section = request.form.get("section", current_user.section)
        current_user.substation = request.form.get("substation", current_user.substation)
        current_user.tariff = request.form.get("tariff", current_user.tariff)
        current_user.connected_load = request.form.get("connected_load", current_user.connected_load)
        current_user.meter_number = request.form.get("meter_number", current_user.meter_number)
        
        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("consumer.profile"))

    return render_template("consumer/profile.html")


# ────────────────── File Complaint ────────────────── #

@consumer.route("/complaint/new", methods=["GET", "POST"])
@login_required
@consumer_required
def new_complaint():
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        category = request.form.get("category")
        location = request.form.get("location")
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")
        priority = request.form.get("priority", "medium")

        # Handle image upload
        image_filename = None
        if "image" in request.files:
            file = request.files["image"]
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Add timestamp to avoid name collisions
                name, ext = os.path.splitext(filename)
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                filename = f"{name}_{timestamp}{ext}"
                upload_folder = current_app.config["UPLOAD_FOLDER"]
                os.makedirs(upload_folder, exist_ok=True)
                file.save(os.path.join(upload_folder, filename))
                image_filename = filename

        complaint = Complaint(
            consumer_id=current_user.id,
            title=title,
            description=description,
            category=category,
            location=location,
            latitude=float(latitude) if latitude else None,
            longitude=float(longitude) if longitude else None,
            priority=priority,
            image=image_filename,
        )

        db.session.add(complaint)
        db.session.commit()

        # Attempt auto-assignment
        from utils.ai_dispatcher import auto_assign_complaint
        success, msg = auto_assign_complaint(complaint.id)
        if success:
            flash(f"Complaint submitted and {msg}", "success")
        else:
            flash("Complaint submitted successfully! It will be reviewed and assigned shortly.", "success")

        return redirect(url_for("consumer.complaint_history"))

    return render_template("consumer/complaint_form.html")


# ────────────────── Complaint History ────────────────── #

@consumer.route("/complaints")
@login_required
@consumer_required
def complaint_history():
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "")
    category = request.args.get("category", "")
    priority = request.args.get("priority", "")
    sort = request.args.get("sort", "newest")

    query = Complaint.query.filter_by(consumer_id=current_user.id)

    if q:
        if q.isdigit():
            query = query.filter(
                or_(Complaint.id == int(q), Complaint.title.ilike(f"%{q}%"))
            )
        else:
            query = query.filter(Complaint.title.ilike(f"%{q}%"))

    if status:
        query = query.filter_by(status=status)
    if category:
        query = query.filter_by(category=category)
    if priority:
        query = query.filter_by(priority=priority)

    if sort == "oldest":
        query = query.order_by(Complaint.created_at.asc())
    elif sort == "priority":
        query = query.order_by(
            case(
                (Complaint.priority == "high", 1),
                (Complaint.priority == "medium", 2),
                (Complaint.priority == "low", 3),
            )
        )
    else:
        query = query.order_by(Complaint.created_at.desc())

    complaints = query.all()

    categories = [
        "power_outage",
        "voltage_issue",
        "meter_problem",
        "billing",
        "new_connection",
        "other",
    ]

    return render_template(
        "consumer/complaint_history.html",
        complaints=complaints,
        q=q,
        status=status,
        category=category,
        priority=priority,
        sort=sort,
        categories=categories,
    )


# ────────────────── Complaint Details ────────────────── #

@consumer.route("/complaint/<int:complaint_id>")
@login_required
@consumer_required
def complaint_details(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)

    # Ensure consumer can only view their own complaints
    if complaint.consumer_id != current_user.id:
        flash("Access denied.", "danger")
        return redirect(url_for("consumer.complaint_history"))

    return render_template(
        "consumer/complaint_details.html",
        complaint=complaint,
    )


# ────────────────── Worker Details ────────────────── #

@consumer.route("/complaint/<int:complaint_id>/worker")
@login_required
@consumer_required
def worker_details(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)

    if complaint.consumer_id != current_user.id:
        flash("Access denied.", "danger")
        return redirect(url_for("consumer.complaint_history"))

    if not complaint.assigned_worker:
        flash("No worker has been assigned yet.", "info")
        return redirect(url_for("consumer.complaint_details", complaint_id=complaint_id))

    return render_template(
        "consumer/worker_details.html",
        complaint=complaint,
        worker=complaint.assigned_worker,
    )


# ────────────────── Feedback ────────────────── #

@consumer.route("/complaint/<int:complaint_id>/feedback", methods=["GET", "POST"])
@login_required
@consumer_required
def feedback(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)

    if complaint.consumer_id != current_user.id:
        flash("Access denied.", "danger")
        return redirect(url_for("consumer.complaint_history"))

    if complaint.status not in ("resolved", "closed"):
        flash("You can only give feedback on resolved complaints.", "warning")
        return redirect(url_for("consumer.complaint_details", complaint_id=complaint_id))

    # Check if feedback already given
    existing = Feedback.query.filter_by(complaint_id=complaint_id).first()
    if existing:
        flash("You have already submitted feedback for this complaint.", "info")
        return redirect(url_for("consumer.complaint_details", complaint_id=complaint_id))

    if request.method == "POST":
        rating = int(request.form.get("rating", 3))
        comment = request.form.get("comment", "")

        fb = Feedback(
            complaint_id=complaint_id,
            consumer_id=current_user.id,
            rating=rating,
            comment=comment,
        )

        # Close complaint after feedback
        complaint.status = "closed"

        db.session.add(fb)
        db.session.commit()

        flash("Thank you for your feedback!", "success")
        return redirect(url_for("consumer.complaint_details", complaint_id=complaint_id))

    return render_template("consumer/feedback.html", complaint=complaint)

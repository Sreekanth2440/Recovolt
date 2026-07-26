from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, json,
)
from flask_login import login_required, current_user
from sqlalchemy import or_
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash

from models import db
from models.user import User
from models.complaint import Complaint
from models.feedback import Feedback
from models.worker import WorkerProfile

admin = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(f):
    """Decorator to restrict access to admins only."""
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.role != "admin":
            flash("Access denied.", "danger")
            return redirect("/")
        return f(*args, **kwargs)

    return decorated


# ────────────────── Dashboard ────────────────── #

@admin.route("/dashboard")
@login_required
@admin_required
def dashboard():
    total_complaints = Complaint.query.count()
    pending = Complaint.query.filter_by(status="pending").count()
    assigned = Complaint.query.filter(
        Complaint.status.in_(["assigned", "in_progress"])
    ).count()
    resolved = Complaint.query.filter(
        Complaint.status.in_(["resolved", "closed"])
    ).count()

    total_users = User.query.filter_by(role="consumer").count()
    total_workers = User.query.filter_by(role="worker").count()
    total_feedbacks = Feedback.query.count()

    recent_complaints = Complaint.query.order_by(
        Complaint.created_at.desc()
    ).limit(10).all()

    return render_template(
        "admin/dashboard.html",
        total_complaints=total_complaints,
        pending=pending,
        assigned=assigned,
        resolved=resolved,
        total_users=total_users,
        total_workers=total_workers,
        total_feedbacks=total_feedbacks,
        recent_complaints=recent_complaints,
    )


COMPLAINT_CATEGORIES = [
    "power_outage",
    "voltage_issue",
    "meter_problem",
    "billing",
    "new_connection",
    "other",
]


def _build_complaints_query():
    """Apply search and filter params to the complaints query."""
    status_filter = request.args.get("status", "all")
    search = request.args.get("q", "").strip()
    category_filter = request.args.get("category", "all")
    priority_filter = request.args.get("priority", "all")
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()

    query = Complaint.query

    if status_filter and status_filter != "all":
        query = query.filter(Complaint.status == status_filter)

    if category_filter and category_filter != "all":
        query = query.filter(Complaint.category == category_filter)

    if priority_filter and priority_filter != "all":
        query = query.filter(Complaint.priority == priority_filter)

    if date_from:
        try:
            start = datetime.strptime(date_from, "%Y-%m-%d").replace(
                tzinfo=timezone.utc
            )
            query = query.filter(Complaint.created_at >= start)
        except ValueError:
            pass

    if date_to:
        try:
            end = datetime.strptime(date_to, "%Y-%m-%d").replace(
                hour=23, minute=59, second=59, tzinfo=timezone.utc
            )
            query = query.filter(Complaint.created_at <= end)
        except ValueError:
            pass

    if search:
        search_filters = [
            Complaint.title.ilike(f"%{search}%"),
            Complaint.location.ilike(f"%{search}%"),
        ]
        if search.isdigit():
            search_filters.append(Complaint.id == int(search))

        matching_consumers = db.session.query(User.id).filter(
            User.role == "consumer",
            or_(
                User.name.ilike(f"%{search}%"),
                User.consumer_number.ilike(f"%{search}%"),
            ),
        )
        search_filters.append(Complaint.consumer_id.in_(matching_consumers))
        query = query.filter(or_(*search_filters))

    return query.order_by(Complaint.created_at.desc())


# ────────────────── All Complaints ────────────────── #

@admin.route("/complaints")
@login_required
@admin_required
def complaints():
    status_filter = request.args.get("status", "all")
    search = request.args.get("q", "").strip()
    category_filter = request.args.get("category", "all")
    priority_filter = request.args.get("priority", "all")
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()

    complaint_list = _build_complaints_query().all()

    return render_template(
        "admin/complaints.html",
        complaints=complaint_list,
        current_filter=status_filter,
        search=search,
        category_filter=category_filter,
        priority_filter=priority_filter,
        date_from=date_from,
        date_to=date_to,
        categories=COMPLAINT_CATEGORIES,
    )


# ────────────────── Complaint Details ────────────────── #

@admin.route("/complaint/<int:complaint_id>")
@login_required
@admin_required
def complaint_details(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    return render_template(
        "admin/complaint_details.html",
        complaint=complaint,
    )


# ────────────────── Assign Worker ────────────────── #

@admin.route("/complaint/<int:complaint_id>/assign", methods=["GET", "POST"])
@login_required
@admin_required
def assign_worker(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)

    if request.method == "POST":
        worker_id = request.form.get("worker_id")
        worker_user = User.query.get(worker_id)

        if not worker_user or worker_user.role != "worker":
            flash("Invalid worker selected.", "danger")
            return redirect(url_for("admin.assign_worker", complaint_id=complaint_id))

        complaint.assigned_worker_id = worker_user.id
        complaint.status = "assigned"

        from models.notification import Notification
        notif = Notification(
            user_id=worker_user.id,
            complaint_id=complaint.id,
            title="New Complaint Assigned!",
            message=f"Admin assigned you to Complaint #{complaint.id} ({complaint.title}) at {complaint.location}."
        )
        db.session.add(notif)
        db.session.commit()

        flash(
            f"Worker {worker_user.name} assigned.",
            "success",
        )
        return redirect(url_for("admin.complaint_details", complaint_id=complaint_id))

    # Get available workers
    workers = User.query.filter_by(role="worker").all()

    return render_template(
        "admin/assign_worker.html",
        complaint=complaint,
        workers=workers,
    )


# ────────────────── Users ────────────────── #

@admin.route("/users")
@login_required
@admin_required
def users():
    user_list = User.query.filter_by(role="consumer").order_by(
        User.created_at.desc()
    ).all()
    return render_template("admin/users.html", users=user_list)


@admin.route("/user/<int:user_id>")
@login_required
@admin_required
def user_details(user_id):
    user = User.query.get_or_404(user_id)
    user_complaints = Complaint.query.filter_by(
        consumer_id=user_id
    ).order_by(Complaint.created_at.desc()).all()

    return render_template(
        "admin/user_details.html",
        user=user,
        complaints=user_complaints,
    )


# ────────────────── Workers ────────────────── #

@admin.route("/workers")
@login_required
@admin_required
def workers():
    worker_list = User.query.filter_by(role="worker").all()
    return render_template("admin/workers.html", workers=worker_list)


@admin.route("/worker/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_worker():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        employee_id = request.form.get("employee_id")
        designation = request.form.get("designation")
        section = request.form.get("section")
        password = request.form.get("password")

        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash("Email already exists.", "danger")
            return redirect(url_for("admin.add_worker"))

        # Check if employee_id already exists
        if User.query.filter_by(employee_id=employee_id).first():
            flash("Employee ID already exists.", "danger")
            return redirect(url_for("admin.add_worker"))

        worker_user = User(
            name=name,
            email=email,
            phone=phone,
            employee_id=employee_id,
            designation=designation,
            section=section,
            role="worker",
        )
        worker_user.set_password(password)

        db.session.add(worker_user)
        db.session.flush()  # Get the user ID

        try:
            latitude = float(request.form.get("latitude"))
        except (TypeError, ValueError):
            latitude = None
            
        try:
            longitude = float(request.form.get("longitude"))
        except (TypeError, ValueError):
            longitude = None

        # Create worker profile
        wp = WorkerProfile(
            user_id=worker_user.id,
            section=section,
            designation=designation,
            latitude=latitude,
            longitude=longitude,
        )
        db.session.add(wp)
        db.session.commit()

        flash(f"Worker {name} added successfully.", "success")
        return redirect(url_for("admin.workers"))

    return render_template("admin/add_worker.html")


@admin.route("/worker/<int:worker_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_worker(worker_id):
    worker_user = User.query.get_or_404(worker_id)

    if worker_user.role != "worker":
        flash("User is not a worker.", "danger")
        return redirect(url_for("admin.workers"))

    if request.method == "POST":
        worker_user.name = request.form.get("name", worker_user.name)
        worker_user.phone = request.form.get("phone", worker_user.phone)
        worker_user.designation = request.form.get("designation", worker_user.designation)
        worker_user.section = request.form.get("section", worker_user.section)

        # Update worker profile too
        if worker_user.worker_profile:
            worker_user.worker_profile.designation = worker_user.designation
            worker_user.worker_profile.section = worker_user.section
            is_available = request.form.get("is_available")
            worker_user.worker_profile.is_available = is_available == "on"
            
            try:
                worker_user.worker_profile.latitude = float(request.form.get("latitude"))
            except (TypeError, ValueError):
                pass
                
            try:
                worker_user.worker_profile.longitude = float(request.form.get("longitude"))
            except (TypeError, ValueError):
                pass

        new_password = request.form.get("password")
        if new_password:
            worker_user.set_password(new_password)

        db.session.commit()
        flash("Worker updated successfully.", "success")
        return redirect(url_for("admin.workers"))

    return render_template("admin/edit_worker.html", worker=worker_user)


# ────────────────── Feedbacks ────────────────── #

@admin.route("/feedbacks")
@login_required
@admin_required
def feedbacks():
    feedback_list = Feedback.query.order_by(
        Feedback.created_at.desc()
    ).all()
    return render_template("admin/feedbacks.html", feedbacks=feedback_list)


# ────────────────── Reports ────────────────── #

@admin.route("/reports")
@login_required
@admin_required
def reports():
    # Status counts
    status_counts = {
        "pending": Complaint.query.filter_by(status="pending").count(),
        "assigned": Complaint.query.filter_by(status="assigned").count(),
        "in_progress": Complaint.query.filter_by(status="in_progress").count(),
        "resolved": Complaint.query.filter_by(status="resolved").count(),
        "closed": Complaint.query.filter_by(status="closed").count(),
    }

    # Category counts
    category_counts = {}
    for cat in COMPLAINT_CATEGORIES:
        category_counts[cat.replace("_", " ").title()] = (
            Complaint.query.filter_by(category=cat).count()
        )

    # Priority counts
    priority_counts = {
        "Low": Complaint.query.filter_by(priority="low").count(),
        "Medium": Complaint.query.filter_by(priority="medium").count(),
        "High": Complaint.query.filter_by(priority="high").count(),
    }

    # Average rating
    all_feedbacks = Feedback.query.all()
    avg_rating = 0
    if all_feedbacks:
        avg_rating = round(
            sum(f.rating for f in all_feedbacks) / len(all_feedbacks), 1
        )

    return render_template(
        "admin/reports.html",
        status_counts=status_counts,
        category_counts=category_counts,
        priority_counts=priority_counts,
        avg_rating=avg_rating,
        total_feedbacks=len(all_feedbacks),
        chart_data=json.dumps({
            "status": {
                "labels": [s.replace("_", " ").title() for s in status_counts],
                "values": list(status_counts.values()),
            },
            "category": {
                "labels": list(category_counts.keys()),
                "values": list(category_counts.values()),
            },
            "priority": {
                "labels": list(priority_counts.keys()),
                "values": list(priority_counts.values()),
            },
        }),
    )

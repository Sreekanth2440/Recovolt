from datetime import datetime, timezone
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash,
)
from flask_login import login_required, current_user

from models import db
from models.complaint import Complaint

worker = Blueprint("worker", __name__, url_prefix="/worker")


def worker_required(f):
    """Decorator to restrict access to workers only."""
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.role != "worker":
            flash("Access denied.", "danger")
            return redirect("/")
        return f(*args, **kwargs)

    return decorated


# ────────────────── Dashboard ────────────────── #

@worker.route("/dashboard")
@login_required
@worker_required
def dashboard():
    assigned = Complaint.query.filter_by(
        assigned_worker_id=current_user.id
    ).order_by(Complaint.created_at.desc()).all()

    total = len(assigned)
    active = sum(1 for c in assigned if c.status in ("assigned", "in_progress"))
    completed = sum(1 for c in assigned if c.status in ("resolved", "closed"))

    active_jobs = [c for c in assigned if c.status in ("assigned", "in_progress")][:5]

    return render_template(
        "worker/dashboard.html",
        total=total,
        active=active,
        completed=completed,
        active_jobs=active_jobs,
    )


# ────────────────── Profile ────────────────── #

@worker.route("/profile", methods=["GET", "POST"])
@login_required
@worker_required
def profile():
    if request.method == "POST":
        current_user.name = request.form.get("name", current_user.name)
        current_user.phone = request.form.get("phone", current_user.phone)
        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("worker.profile"))

    return render_template("worker/profile.html")


# ────────────────── Assigned Jobs ────────────────── #

@worker.route("/jobs")
@login_required
@worker_required
def assigned_jobs():
    jobs = Complaint.query.filter(
        Complaint.assigned_worker_id == current_user.id,
        Complaint.status.in_(["assigned", "in_progress"]),
    ).order_by(Complaint.created_at.desc()).all()

    return render_template("worker/assigned_jobs.html", jobs=jobs)


# ────────────────── Completed Jobs ────────────────── #

@worker.route("/jobs/completed")
@login_required
@worker_required
def completed_jobs():
    jobs = Complaint.query.filter(
        Complaint.assigned_worker_id == current_user.id,
        Complaint.status.in_(["resolved", "closed"]),
    ).order_by(Complaint.resolved_at.desc()).all()

    return render_template("worker/completed_jobs.html", jobs=jobs)


# ────────────────── Complaint Details ────────────────── #

@worker.route("/complaint/<int:complaint_id>")
@login_required
@worker_required
def complaint_details(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)

    if complaint.assigned_worker_id != current_user.id:
        flash("Access denied.", "danger")
        return redirect(url_for("worker.assigned_jobs"))

    return render_template(
        "worker/complaint_details.html",
        complaint=complaint,
    )


# ────────────────── Update Status ────────────────── #

@worker.route("/complaint/<int:complaint_id>/update", methods=["GET", "POST"])
@login_required
@worker_required
def update_status(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)

    if complaint.assigned_worker_id != current_user.id:
        flash("Access denied.", "danger")
        return redirect(url_for("worker.assigned_jobs"))

    if request.method == "POST":
        new_status = request.form.get("status")
        notes = request.form.get("notes", "")

        if not new_status:
            flash("Error: System did not receive a new status from the form dropdown.", "danger")
            return redirect(url_for("worker.update_status", complaint_id=complaint_id))

        old_status = complaint.status
        complaint.status = new_status
        complaint.updated_at = datetime.now(timezone.utc)

        if new_status == "resolved":
            complaint.resolved_at = datetime.now(timezone.utc)

        try:
            db.session.commit()
            if new_status == "resolved":
                flash(f"Complaint marked as resolved successfully.", "success")
            elif new_status != old_status:
                flash(f"Status updated from {old_status} to {new_status}.", "success")
            else:
                flash("Status is already set to that value.", "info")
        except Exception as e:
            db.session.rollback()
            flash(f"Database Error: {str(e)}", "danger")

        return redirect(url_for("worker.complaint_details", complaint_id=complaint_id))

    return render_template("worker/update_status.html", complaint=complaint)

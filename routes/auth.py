from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

from models import db
from models.user import User

auth = Blueprint("auth", __name__)


# ---------------- Register ---------------- #

@auth.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        consumer_number = request.form.get("consumer_number")
        section = request.form.get("section", "Perumbavoor Section 5583")
        password = request.form.get("password")

        existing = User.query.filter_by(email=email).first()

        if existing:
            flash("Email already exists.", "danger")
            return redirect(url_for("auth.register"))

        user = User(
            name=name,
            email=email,
            phone=phone,
            consumer_number=consumer_number,
            section=section,
            role="consumer"
        )

        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash("Registration successful. Please login.", "success")

        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


# ---------------- Login ---------------- #

@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):

            login_user(user)

            if user.role == "admin":
                return redirect("/admin/dashboard")

            elif user.role == "worker":
                return redirect("/worker/dashboard")

            else:
                return redirect("/consumer/dashboard")

        flash("Invalid Email or Password", "danger")

    return render_template("auth/login.html")


# ---------------- Logout ---------------- #

@auth.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(url_for("auth.login"))
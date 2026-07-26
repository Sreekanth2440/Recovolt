"""
Comprehensive seed script to populate RecoVolt with realistic test data.
Run: python seed.py
"""

from datetime import datetime, timezone, timedelta
from app import create_app
from models import db
from models.user import User
from models.complaint import Complaint
from models.feedback import Feedback
from models.worker import WorkerProfile

app = create_app()

with app.app_context():
    db.create_all()

    # Clear existing data (order matters for FK constraints)
    Feedback.query.delete()
    Complaint.query.delete()
    WorkerProfile.query.delete()
    User.query.delete()
    db.session.commit()
    print("🗑️  Cleared existing data.\n")

    now = datetime.now(timezone.utc)

    # ─────────────────────────────────────────────
    # 1. ADMIN
    # ─────────────────────────────────────────────
    admin = User(
        name="Admin",
        email="admin@recovolt.com",
        phone="9447001001",
        role="admin",
    )
    admin.set_password("admin123")
    db.session.add(admin)
    db.session.flush()
    print(f"✅ Admin  : admin@recovolt.com / admin123")

    # ─────────────────────────────────────────────
    # 2. CONSUMERS
    # ─────────────────────────────────────────────
    consumers_data = [
        {"name": "Arun Kumar",       "email": "arun@gmail.com",       "phone": "9447101001", "consumer_number": "KSEB-1001"},
        {"name": "Priya Menon",      "email": "priya@gmail.com",      "phone": "9447101002", "consumer_number": "KSEB-1002"},
        {"name": "Rajesh Nair",      "email": "rajesh@gmail.com",     "phone": "9447101003", "consumer_number": "KSEB-1003"},
        {"name": "Lakshmi Devi",     "email": "lakshmi@gmail.com",    "phone": "9447101004", "consumer_number": "KSEB-1004"},
        {"name": "Mohammed Faisal",  "email": "faisal@gmail.com",     "phone": "9447101005", "consumer_number": "KSEB-1005"},
    ]

    consumers = []
    for cd in consumers_data:
        c = User(role="consumer", **cd, created_at=now - timedelta(days=60))
        c.set_password("user123")
        db.session.add(c)
        consumers.append(c)
    db.session.flush()
    print(f"✅ Created {len(consumers)} consumers (password: user123)")

    # ─────────────────────────────────────────────
    # 3. WORKERS
    # ─────────────────────────────────────────────
    workers_data = [
        {"name": "Suresh Babu",    "email": "suresh@kseb.in",   "phone": "9447201001", "employee_id": "EMP1001", "designation": "Line Worker",       "section": "Thiruvananthapuram North"},
        {"name": "Vineeth Kumar",  "email": "vineeth@kseb.in",  "phone": "9447201002", "employee_id": "EMP1002", "designation": "Senior Electrician", "section": "Ernakulam Central"},
        {"name": "Manoj S",        "email": "manoj@kseb.in",    "phone": "9447201003", "employee_id": "EMP1003", "designation": "Meter Technician",   "section": "Kozhikode South"},
        {"name": "Anitha R",       "email": "anitha@kseb.in",   "phone": "9447201004", "employee_id": "EMP1004", "designation": "Field Engineer",     "section": "Thrissur East"},
    ]

    workers = []
    for wd in workers_data:
        w = User(role="worker", **wd, created_at=now - timedelta(days=90))
        w.set_password("worker123")
        db.session.add(w)
        workers.append(w)
    db.session.flush()

    # Create WorkerProfile for each worker
    for w in workers:
        wp = WorkerProfile(user_id=w.id, section=w.section, designation=w.designation, is_available=True)
        db.session.add(wp)
    db.session.flush()
    print(f"✅ Created {len(workers)} workers (password: worker123)")

    # ─────────────────────────────────────────────
    # 4. COMPLAINTS (various statuses)
    # ─────────────────────────────────────────────
    complaints_data = [
        # PENDING complaints
        {
            "consumer": consumers[0], "title": "Frequent power outages in Kowdiar area",
            "description": "Power goes off at least 3-4 times daily for 30 minutes each. This has been happening for the past two weeks. It's affecting our daily life and work-from-home setup. The UPS backup drains out quickly.",
            "category": "power_outage", "location": "Kowdiar, Thiruvananthapuram", "priority": "high",
            "status": "pending", "days_ago": 2,
        },
        {
            "consumer": consumers[1], "title": "Electricity meter showing wrong readings",
            "description": "My meter has been showing abnormally high readings since last month. My usage hasn't changed but the bill has doubled. I suspect the meter is faulty and needs replacement or recalibration.",
            "category": "meter_problem", "location": "Panampilly Nagar, Ernakulam", "priority": "medium",
            "status": "pending", "days_ago": 1,
        },
        {
            "consumer": consumers[4], "title": "Sparking from overhead transformer",
            "description": "There is visible sparking from the transformer near our house, especially during rain. This is extremely dangerous and needs immediate attention. Nearby residents are also concerned about safety.",
            "category": "power_outage", "location": "Mavoor Road, Kozhikode", "priority": "high",
            "status": "pending", "days_ago": 0,
        },

        # ASSIGNED complaints
        {
            "consumer": consumers[2], "title": "Voltage fluctuation damaging appliances",
            "description": "Severe voltage fluctuations throughout the day. My refrigerator compressor and air conditioner have already been damaged. The voltage drops to as low as 160V during peak hours.",
            "category": "voltage_issue", "location": "Marine Drive, Ernakulam", "priority": "high",
            "status": "assigned", "worker": workers[1], "days_ago": 5,
        },
        {
            "consumer": consumers[3], "title": "New connection request for house construction",
            "description": "I have completed the construction of my new house and need a fresh electricity connection. All required documents including ownership certificate and approved building plan are ready.",
            "category": "new_connection", "location": "Swaraj Round, Thrissur", "priority": "low",
            "status": "assigned", "worker": workers[3], "days_ago": 7,
        },

        # IN_PROGRESS complaints
        {
            "consumer": consumers[0], "title": "Street light not working near school",
            "description": "The main street light near Government LP School, Vazhuthacaud has not been working for over a month. This road is used by children and commuters and it's very dark and unsafe at night.",
            "category": "other", "location": "Vazhuthacaud, Thiruvananthapuram", "priority": "medium",
            "status": "in_progress", "worker": workers[0], "days_ago": 10,
        },
        {
            "consumer": consumers[1], "title": "Billing discrepancy in last 3 months",
            "description": "I have been consistently overcharged in my electricity bills for the past three months. Despite minimal usage during summer vacation (family was away), bills show 450+ units each month.",
            "category": "billing", "location": "Kadavanthra, Ernakulam", "priority": "medium",
            "status": "in_progress", "worker": workers[1], "days_ago": 8,
        },

        # RESOLVED complaints
        {
            "consumer": consumers[2], "title": "Power line fallen on road after storm",
            "description": "A heavy storm brought down a power line on the main road near Calicut Beach. The wire is lying on the road and is extremely dangerous. Emergency response needed.",
            "category": "power_outage", "location": "Beach Road, Kozhikode", "priority": "high",
            "status": "resolved", "worker": workers[2], "days_ago": 15, "resolved_days_ago": 13,
        },
        {
            "consumer": consumers[3], "title": "Meter box damaged by recent flooding",
            "description": "The recent flooding in our area has completely damaged the external meter box. Water has seeped into the wiring and the meter is no longer functional. Need a complete replacement.",
            "category": "meter_problem", "location": "Ayyanthole, Thrissur", "priority": "high",
            "status": "resolved", "worker": workers[3], "days_ago": 20, "resolved_days_ago": 16,
        },
        {
            "consumer": consumers[4], "title": "Request for load enhancement",
            "description": "I need to upgrade my connection from single phase to three phase for my newly started bakery business at home. Current 2kW connection is insufficient for the commercial equipment.",
            "category": "new_connection", "location": "SM Street, Kozhikode", "priority": "low",
            "status": "resolved", "worker": workers[2], "days_ago": 25, "resolved_days_ago": 18,
        },

        # CLOSED complaints
        {
            "consumer": consumers[0], "title": "Broken electric pole leaning dangerously",
            "description": "An old wooden electric pole near our lane has cracked at the base and is leaning at a 30-degree angle. Multiple wires are attached to it and it could collapse anytime causing serious damage.",
            "category": "power_outage", "location": "Pattom, Thiruvananthapuram", "priority": "high",
            "status": "closed", "worker": workers[0], "days_ago": 30, "resolved_days_ago": 26,
        },
        {
            "consumer": consumers[2], "title": "Underground cable fault causing outage",
            "description": "There seems to be a fault in the underground cable in our colony. The entire area of about 50 houses has been without power intermittently. Temporary fixes haven't helped.",
            "category": "power_outage", "location": "HiLite City, Kozhikode", "priority": "medium",
            "status": "closed", "worker": workers[2], "days_ago": 35, "resolved_days_ago": 30,
        },
    ]

    complaints = []
    for cd in complaints_data:
        c = Complaint(
            consumer_id=cd["consumer"].id,
            title=cd["title"],
            description=cd["description"],
            category=cd["category"],
            location=cd["location"],
            priority=cd["priority"],
            status=cd["status"],
            assigned_worker_id=cd.get("worker", None) and cd["worker"].id,
            created_at=now - timedelta(days=cd["days_ago"]),
            updated_at=now - timedelta(days=max(cd["days_ago"] - 1, 0)),
            resolved_at=(now - timedelta(days=cd["resolved_days_ago"])) if cd.get("resolved_days_ago") else None,
        )
        db.session.add(c)
        complaints.append(c)
    db.session.flush()
    print(f"✅ Created {len(complaints)} complaints")

    # ─────────────────────────────────────────────
    # 5. FEEDBACKS (on resolved/closed complaints)
    # ─────────────────────────────────────────────
    feedbacks_data = [
        {"complaint_idx": 7,  "rating": 5, "comment": "Excellent response! The team arrived within hours and fixed the fallen power line. Very professional and safety-conscious."},
        {"complaint_idx": 8,  "rating": 4, "comment": "Good service. The meter was replaced efficiently. Only took a day longer than expected."},
        {"complaint_idx": 9,  "rating": 3, "comment": "The load enhancement was done but the process took longer than communicated. Paperwork could be streamlined."},
        {"complaint_idx": 10, "rating": 5, "comment": "Outstanding emergency response! The dangerous pole was replaced with a new concrete pole within 24 hours. Kudos to the team!"},
        {"complaint_idx": 11, "rating": 4, "comment": "The underground cable issue was complex but the team handled it well. Power is now stable in our colony."},
    ]

    for fd in feedbacks_data:
        comp = complaints[fd["complaint_idx"]]
        f = Feedback(
            complaint_id=comp.id,
            consumer_id=comp.consumer_id,
            rating=fd["rating"],
            comment=fd["comment"],
            created_at=comp.resolved_at + timedelta(days=1) if comp.resolved_at else now,
        )
        db.session.add(f)
    db.session.flush()
    print(f"✅ Created {len(feedbacks_data)} feedbacks")

    db.session.commit()

    # ─────────────────────────────────────────────
    # SUMMARY
    # ─────────────────────────────────────────────
    print("\n" + "=" * 50)
    print("  🎉 SEED DATA LOADED SUCCESSFULLY!")
    print("=" * 50)
    print("\n  🔑 LOGIN CREDENTIALS:")
    print("  ─────────────────────────────────────")
    print("  ADMIN:")
    print("    Email:    admin@recovolt.com")
    print("    Password: admin123")
    print("\n  CONSUMERS (all use password: user123):")
    for c in consumers:
        print(f"    {c.name:20s} → {c.email}")
    print("\n  WORKERS (all use password: worker123):")
    for w in workers:
        print(f"    {w.name:20s} → {w.email} ({w.employee_id})")
    print("\n  📊 DATA SUMMARY:")
    print(f"    Complaints: {len(complaints)} (3 pending, 2 assigned, 2 in-progress, 3 resolved, 2 closed)")
    print(f"    Feedbacks:  {len(feedbacks_data)}")
    print("=" * 50)

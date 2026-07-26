# RecoVolt — KSEB Complaint Management System

## What Is This Project?

**RecoVolt** is a next-generation full-stack web application that digitises the complaint management workflow for **KSEB (Kerala State Electricity Board)**. 

Recently upgraded with a **Premium Glassmorphism UI (Tailwind CSS)**, an **AI Smart Auto-Assignment Algorithm**, **Real-time Chat**, and **Live GPS Mapping**, it provides a seamless experience for consumers, administrators, and field workers.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend Framework** | Flask 3.1 (Python) |
| **Database** | MySQL via PyMySQL |
| **ORM** | SQLAlchemy 2.0 (Flask-SQLAlchemy) |
| **Migrations** | Alembic (Flask-Migrate) |
| **Authentication** | Flask-Login (session-based) |
| **Password Hashing** | Werkzeug `generate_password_hash` / `check_password_hash` |
| **Email Notifications** | Flask-Mail (SMTP, defaults to Gmail) |
| **Forms / Validation** | Flask-WTF + WTForms + email-validator |
| **Frontend** | Jinja2 templates, Tailwind CSS (via CDN), Google Material Symbols, Leaflet.js (Maps) |
| **Styling** | Custom Glassmorphism UI + Tailwind utilities |
| **File Uploads** | Werkzeug `secure_filename`, stored in `uploads/` |

---

## User Roles & Permissions

The application has **three roles**, each with its own dashboard, sidebar, and route group:

| Role | Description |
|---|---|
| **Consumer** (`consumer`) | An electricity consumer who registers, files complaints, tracks status, views assigned worker info, and submits feedback after resolution. |
| **Worker** (`worker`) | A KSEB field employee who views assigned complaints, updates their status (in_progress → resolved), and triggers consumer email notifications. |
| **Admin** (`admin`) | A KSEB administrator who views all complaints, assigns workers to complaints, manages workers (add/edit), views consumers, reads feedbacks, and generates reports with charts. |

### Role-Based Access Control

Each blueprint has a decorator (`consumer_required`, `worker_required`, `admin_required`) that checks `current_user.role` before granting access. Unauthorized users are redirected to `/` with a flash message.

---

## Database Schema (Models)

### `User` (`users` table) — [`models/user.py`](models/user.py)

The single user table for all three roles.

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | Auto-increment |
| `name` | String(100) | Required |
| `email` | String(120) | Unique, required |
| `phone` | String(20) | Required |
| `password` | String(255) | Hashed via Werkzeug |
| `role` | String(20) | `"consumer"`, `"worker"`, or `"admin"` |
| `consumer_number` | String(50) | Unique, nullable — only for consumers |
| `employee_id` | String(50) | Unique, nullable — only for workers |
| `designation` | String(100) | Nullable — only for workers |
| `section` | String(100) | Nullable — only for workers |
| `created_at` | DateTime | UTC default |

### `Complaint` (`complaints` table) — [`models/complaint.py`](models/complaint.py)

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | Auto-increment |
| `consumer_id` | FK → `users.id` | The consumer who filed it |
| `title` | String(200) | Required |
| `description` | Text | Required |
| `category` | String(50) | One of: `power_outage`, `voltage_issue`, `meter_problem`, `billing`, `new_connection`, `other` |
| `location` | String(255) | Required |
| `image` | String(255) | Nullable — filename of uploaded image |
| `status` | String(20) | Flow: `pending` → `assigned` → `in_progress` → `resolved` → `closed` |
| `priority` | String(10) | `low`, `medium`, `high` (default: `medium`) |
| `assigned_worker_id` | FK → `users.id` | Nullable — set when admin assigns |
| `created_at` | DateTime | UTC |
| `updated_at` | DateTime | UTC, auto-updates |
| `resolved_at` | DateTime | Nullable — set when worker resolves |

**Relationships:** `consumer` (User), `assigned_worker` (User), `feedback` (one-to-one), `activities` (one-to-many, ordered desc).

**Helper properties:** `status_display`, `category_display`, `priority_badge`, `status_badge` — return human-readable strings and Bootstrap CSS classes.

### `ComplaintActivity` (`complaint_activities` table) — [`models/complaint_activity.py`](models/complaint_activity.py)

An audit log for every status change or note on a complaint.

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `complaint_id` | FK → `complaints.id` | |
| `user_id` | FK → `users.id` | Who made the change |
| `old_status` | String(20) | Nullable |
| `new_status` | String(20) | Nullable |
| `notes` | Text | Nullable — free-text notes |
| `created_at` | DateTime | UTC |

### `Feedback` (`feedbacks` table) — [`models/feedback.py`](models/feedback.py)

One feedback per complaint (one-to-one). Consumers submit this after resolution.

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `complaint_id` | FK → `complaints.id` | Unique |
| `consumer_id` | FK → `users.id` | |
| `rating` | Integer | 1–5 star rating |
| `comment` | Text | Nullable |
| `created_at` | DateTime | UTC |

### `WorkerProfile` (`worker_profiles` table) — [`models/worker.py`](models/worker.py)

Extended profile for workers (one-to-one with User).

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `user_id` | FK → `users.id` | Unique |
| `section` | String(100) | Nullable |
| `designation` | String(100) | Nullable |
| `is_available` | Boolean | Default `True` |

### `Message` (`messages` table) — [`models/complaint.py`](models/complaint.py)

A live chat system enabling direct communication between consumers, workers, and admins per complaint.

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `complaint_id` | FK → `complaints.id` | |
| `sender_id` | FK → `users.id` | |
| `content` | Text | The message text |
| `created_at` | DateTime | UTC |

---

## 🌟 Key Features

1. **AI Smart Auto-Assignment**: Uses the Haversine formula to calculate the distance between a complaint's GPS coordinates and available field workers. Automatically assigns jobs based on skill match (designation), proximity, and workload balancing.
2. **Real-Time Complaint Chat**: Every complaint features a live messaging channel for consumers, workers, and admins to communicate instantly.
3. **Interactive GPS Maps**: Integrated with Leaflet.js, allowing consumers to pinpoint exact locations using their device's GPS when filing a complaint.
4. **Premium Glassmorphism UI**: Completely restyled using modern web design principles—featuring dynamic gradients, hover micro-animations, blur effects, and card-based grids (no traditional tables).
5. **Activity Audit Log**: Every status change is recorded via `log_complaint_activity()`.

---

## Project Structure

```
Recovolt/
├── app.py                  # Flask app factory (create_app), home/track/about/contact routes, error handlers
├── config.py               # Config class (DB URI, upload folder, mail settings, secret key)
├── run.py                  # Entry point: imports app and runs debug server
├── seed.py                 # One-time script to create default admin user (admin@recovolt.com / admin123)
├── requirements.txt        # Pinned Python dependencies
├── pyrightconfig.json      # Type checker config (points to local venv)
│
├── models/
│   ├── __init__.py          # Creates db (SQLAlchemy) & login_manager; imports all models
│   ├── user.py              # User model (all roles) + Flask-Login user_loader
│   ├── complaint.py         # Complaint model + helper properties
│   ├── complaint_activity.py # ComplaintActivity audit log model
│   ├── feedback.py          # Feedback model (1-to-1 with Complaint)
│   └── worker.py            # WorkerProfile model (1-to-1 with User)
│
├── routes/
│   ├── __init__.py          # Empty (package marker)
│   ├── auth.py              # Blueprint "auth": /register, /login, /logout
│   ├── consumer.py          # Blueprint "consumer": /consumer/dashboard, /consumer/complaints, etc.
│   ├── worker.py            # Blueprint "worker": /worker/dashboard, /worker/jobs, etc.
│   ├── admin.py             # Blueprint "admin": /admin/dashboard, /admin/complaints, etc.
│   ├── complaint.py         # Placeholder (unused — complaint routes live in consumer/admin)
│   └── feedback.py          # Placeholder (unused — feedback routes live in consumer)
│
├── utils/
│   ├── __init__.py          # Empty
│   ├── activity.py          # log_complaint_activity() — creates ComplaintActivity records
│   └── notifications.py     # Email notification helpers (worker assigned, complaint resolved, status update)
│
├── templates/
│   ├── base.html            # Master layout: navbar, sidebar (auth'd), flash messages, footer, Bootstrap/JS
│   ├── index.html           # Public landing page: hero, live stats, feature cards, testimonials, FAQ
│   ├── track.html           # Public complaint tracker (ID + email/phone lookup)
│   ├── about.html           # Static about page
│   ├── contact.html         # Static contact page
│   ├── includes/
│   │   ├── navbar.html      # Top navigation bar
│   │   ├── sidebar.html     # Role-based sidebar (consumer/worker/admin)
│   │   └── footer.html      # Page footer
│   ├── auth/
│   │   ├── login.html
│   │   ├── register.html
│   │   └── forgot_password.html
│   ├── consumer/
│   │   ├── dashboard.html       # Stats cards, chart, recent complaints
│   │   ├── complaint_form.html  # New complaint form (with image upload)
│   │   ├── complaint_history.html # Filterable/searchable complaint list
│   │   ├── complaint_details.html # Single complaint view + activity timeline
│   │   ├── worker_details.html   # Assigned worker info
│   │   ├── feedback.html         # Star rating + comment form
│   │   └── profile.html          # Edit name/phone
│   ├── worker/
│   │   ├── dashboard.html        # Stats + active jobs
│   │   ├── assigned_jobs.html    # List of active assignments
│   │   ├── completed_jobs.html   # List of resolved/closed jobs
│   │   ├── complaint_details.html # Complaint detail view
│   │   ├── update_status.html    # Status transition form + notes
│   │   └── profile.html          # Edit name/phone
│   ├── admin/
│   │   ├── dashboard.html        # KPI cards + recent complaints table
│   │   ├── complaints.html       # All complaints (search/filter by status, category, priority, date)
│   │   ├── complaint_details.html # Complaint detail + activity log
│   │   ├── assign_worker.html    # Assign a worker to a complaint
│   │   ├── users.html            # Consumer list
│   │   ├── user_details.html     # Consumer profile + their complaints
│   │   ├── workers.html          # Worker list
│   │   ├── add_worker.html       # Add new worker form
│   │   ├── edit_worker.html      # Edit worker form
│   │   ├── feedbacks.html        # All feedback list
│   │   └── reports.html          # Charts: status, category, priority distribution + avg rating
│   ├── email/
│   │   ├── worker_assigned.html   # Email to worker on assignment
│   │   ├── complaint_resolved.html # Email to consumer on resolution
│   │   └── status_update.html     # Email to consumer on status change
│   └── errors/
│       ├── 404.html
│       └── 500.html
│
├── static/
│   ├── css/
│   │   └── style.css         # All custom styles (17 KB), supports light/dark theme via data-theme attribute
│   └── js/
│       ├── main.js           # Theme toggle, sidebar toggle, general UI helpers
│       ├── validation.js     # Client-side form validation
│       ├── admin.js          # Admin-specific JS (charts, filters)
│       ├── consumer.js       # Consumer-specific JS (dashboard charts)
│       └── worker.js         # Worker-specific JS
│
├── uploads/                  # User-uploaded complaint images (gitignored in production)
├── migrations/               # Alembic migration directory (currently empty — using db.create_all())
└── venv/                     # Python virtual environment
```

---

## Route Map

### Public Routes (no auth required)

| Method | URL | Handler | Description |
|---|---|---|---|
| GET | `/` | `app.home` | Landing page with live stats, features, testimonials, FAQ |
| GET/POST | `/track` | `app.track` | Public complaint tracker (by ID + email/phone) |
| GET | `/about` | `app.about` | About page |
| GET | `/contact` | `app.contact` | Contact page |

### Auth Routes — Blueprint `auth`

| Method | URL | Handler | Description |
|---|---|---|---|
| GET/POST | `/register` | `auth.register` | Consumer self-registration |
| GET/POST | `/login` | `auth.login` | Login (redirects by role) |
| GET | `/logout` | `auth.logout` | Logout (requires login) |

### Consumer Routes — Blueprint `consumer` (prefix: `/consumer`)

| Method | URL | Handler | Description |
|---|---|---|---|
| GET | `/consumer/dashboard` | `consumer.dashboard` | Consumer dashboard with stats and chart |
| GET/POST | `/consumer/profile` | `consumer.profile` | Edit profile |
| GET/POST | `/consumer/complaint/new` | `consumer.new_complaint` | File a new complaint (with optional image) |
| GET | `/consumer/complaints` | `consumer.complaint_history` | List own complaints (search, filter, sort) |
| GET | `/consumer/complaint/<id>` | `consumer.complaint_details` | View complaint details + activity timeline |
| GET | `/consumer/complaint/<id>/worker` | `consumer.worker_details` | View assigned worker info |
| GET/POST | `/consumer/complaint/<id>/feedback` | `consumer.feedback` | Submit feedback (1–5 stars + comment) |

### Worker Routes — Blueprint `worker` (prefix: `/worker`)

| Method | URL | Handler | Description |
|---|---|---|---|
| GET | `/worker/dashboard` | `worker.dashboard` | Worker dashboard with active/completed stats |
| GET/POST | `/worker/profile` | `worker.profile` | Edit profile |
| GET | `/worker/jobs` | `worker.assigned_jobs` | Active assignments list |
| GET | `/worker/jobs/completed` | `worker.completed_jobs` | Completed jobs list |
| GET | `/worker/complaint/<id>` | `worker.complaint_details` | View complaint details |
| GET/POST | `/worker/complaint/<id>/update` | `worker.update_status` | Update status + notes (triggers email) |

### Admin Routes — Blueprint `admin` (prefix: `/admin`)

| Method | URL | Handler | Description |
|---|---|---|---|
| GET | `/admin/dashboard` | `admin.dashboard` | Admin dashboard with all KPIs |
| GET | `/admin/complaints` | `admin.complaints` | All complaints (search, multi-filter) |
| GET | `/admin/complaint/<id>` | `admin.complaint_details` | Complaint detail + activity log |
| GET/POST | `/admin/complaint/<id>/assign` | `admin.assign_worker` | Assign worker to complaint |
| GET | `/admin/users` | `admin.users` | Consumer list |
| GET | `/admin/user/<id>` | `admin.user_details` | Consumer detail + their complaints |
| GET | `/admin/workers` | `admin.workers` | Worker list |
| GET/POST | `/admin/worker/add` | `admin.add_worker` | Add new worker |
| GET/POST | `/admin/worker/<id>/edit` | `admin.edit_worker` | Edit existing worker |
| GET | `/admin/feedbacks` | `admin.feedbacks` | All feedback list |
| GET | `/admin/reports` | `admin.reports` | Analytics: status/category/priority charts, avg rating |

---

## Complaint Lifecycle

```
Consumer files complaint
        │
        ▼
    ┌─────────┐
    │ PENDING  │  ← Default status on creation
    └────┬────┘
         │  Admin assigns a worker
         ▼
    ┌──────────┐
    │ ASSIGNED │  ← Worker receives email notification
    └────┬─────┘
         │  Worker starts work
         ▼
    ┌─────────────┐
    │ IN_PROGRESS │  ← Consumer notified via email
    └──────┬──────┘
           │  Worker resolves
           ▼
    ┌──────────┐
    │ RESOLVED │  ← Consumer notified, can now submit feedback
    └────┬─────┘
         │  Consumer submits feedback (1–5 stars)
         ▼
    ┌────────┐
    │ CLOSED │  ← Final state
    └────────┘
```

Every status transition is logged in `complaint_activities` with the acting user, old/new status, and optional notes.

---

## Email Notification System

Located in [`utils/notifications.py`](utils/notifications.py). Uses Flask-Mail with SMTP (Gmail by default). Falls back to console logging if `MAIL_USERNAME` is not configured.

**Three notification types:**
1. **Worker Assigned** — sent to the worker when admin assigns them a complaint
2. **Complaint Resolved** — sent to the consumer when worker marks the complaint resolved
3. **Status Update** — sent to the consumer on any other status change

Each notification has a corresponding HTML email template in `templates/email/`.

---

## Configuration

All settings are in [`config.py`](config.py), loaded via environment variables with sensible defaults:

| Setting | Env Var | Default |
|---|---|---|
| `SECRET_KEY` | `SECRET_KEY` | `"recovolt_secret_key"` |
| `SQLALCHEMY_DATABASE_URI` | `DATABASE_URL` | `mysql+pymysql://root:root@localhost/recovolt_db` |
| `UPLOAD_FOLDER` | — | `<project_root>/uploads` |
| `MAX_CONTENT_LENGTH` | — | 5 MB |
| `MAIL_SERVER` | `MAIL_SERVER` | `smtp.gmail.com` |
| `MAIL_PORT` | `MAIL_PORT` | `587` |
| `MAIL_USE_TLS` | — | `True` |
| `MAIL_USERNAME` | `MAIL_USERNAME` | `None` |
| `MAIL_PASSWORD` | `MAIL_PASSWORD` | `None` |
| `MAIL_DEFAULT_SENDER` | — | `("RecoVolt KSEB", <MAIL_USERNAME>)` |

---

## How to Run

### Prerequisites
- Python 3.10+
- MySQL server running locally
- Create a database: `CREATE DATABASE recovolt_db;`

### Setup

```bash
# Clone and enter the project
cd Recovolt

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Seed the admin user (run once)
python seed.py
# → Creates: admin@recovolt.com / admin123

# Start the dev server
python run.py
# → http://127.0.0.1:5000
```

### Default Admin Credentials
- **Email:** `admin@recovolt.com`
- **Password:** `admin123`

---

## Frontend Architecture

- **Templating:** Jinja2 with template inheritance from `base.html`
- **CSS Framework:** Bootstrap 5.3.7 (CDN) + custom CSS in `static/css/style.css`
- **Icons:** Bootstrap Icons 1.11.3 (CDN)
- **Theme:** Light/dark mode toggle via `data-theme` attribute on `<html>`, persisted in `localStorage` (`recovolt-theme`)
- **Layout:** Authenticated users see a sidebar + main content layout; public pages render without sidebar
- **JavaScript:** Vanilla JS split by role (`main.js`, `admin.js`, `consumer.js`, `worker.js`, `validation.js`)

---

## Key Design Decisions & Conventions

1. **Single `User` model for all roles** — differentiated by the `role` column. Consumer-specific fields (`consumer_number`) and worker-specific fields (`employee_id`, `designation`, `section`) are nullable.
2. **App Factory Pattern** — `create_app()` in `app.py` creates and configures the Flask app. Blueprints are registered inside the factory.
3. **Blueprint per role** — `auth`, `consumer`, `worker`, `admin` each have their own file in `routes/` with a URL prefix.
4. **Activity audit log** — every status change is recorded via `log_complaint_activity()` in `utils/activity.py`.
5. **Graceful email fallback** — if SMTP is not configured, notifications are logged to console instead of crashing.
6. **Image uploads** — timestamped filenames to avoid collisions, stored in `uploads/`, restricted to `png/jpg/jpeg/gif/webp`, max 5 MB.
7. **No REST API** — the app uses server-rendered Jinja2 templates with traditional form submissions (POST → redirect → GET pattern).
8. **Database creation** — `db.create_all()` is called inside the app factory (no Alembic migrations are currently used despite Flask-Migrate being installed).

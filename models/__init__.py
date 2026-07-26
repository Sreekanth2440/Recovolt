# pyrefly: ignore [missing-import]
from flask_sqlalchemy import SQLAlchemy
# pyrefly: ignore [missing-import]
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"

# Import all models so db.create_all() can discover them
from models.user import User  # noqa: F401, E402
from models.complaint import Complaint  # noqa: F401, E402
from models.feedback import Feedback  # noqa: F401, E402
from models.worker import WorkerProfile  # noqa: F401, E402
from models.notification import Notification  # noqa: F401, E402
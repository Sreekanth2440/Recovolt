import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "recovolt_secret_key")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///recovolt.db",
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # File uploads
    UPLOAD_FOLDER = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "uploads"
    )
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB max
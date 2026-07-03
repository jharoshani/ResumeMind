from flask import Flask
from authlib.integrations.flask_client import OAuth
from pymongo import MongoClient
from config import Config


def create_app():
    """Flask application factory."""
    app = Flask(__name__)

    # --- Load configuration ---
    app.secret_key = Config.SECRET_KEY
    app.config["GOOGLE_REDIRECT_URI"] = Config.GOOGLE_REDIRECT_URI
    app.config["MAX_RESUMES"] = Config.MAX_RESUMES
    app.config["MAX_JD_WORDS"] = Config.MAX_JD_WORDS
    app.config["MAX_FILE_SIZE_MB"] = Config.MAX_FILE_SIZE_MB

    # --- Initialize MongoDB ---
    mongo_client = MongoClient(Config.MONGO_URI)
    db = mongo_client[Config.MONGO_DB_NAME]
    app.config["DB"] = db

    # --- Initialize OAuth ---
    oauth = OAuth(app)
    oauth.register(
        name="google",
        client_id=Config.GOOGLE_CLIENT_ID,
        client_secret=Config.GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

    # --- Register Blueprints ---
    from routes.auth_routes import auth_bp
    from routes.page_routes import page_bp
    from routes.api_routes import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(page_bp)
    app.register_blueprint(api_bp)

    return app


# --- Run the app ---
app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)

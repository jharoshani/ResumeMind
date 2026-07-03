from flask import Blueprint, redirect, url_for, session, current_app

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login")
def login():
    """Redirect user to Google OAuth consent screen."""
    oauth = current_app.extensions["authlib.integrations.flask_client"]
    google = oauth.google
    redirect_uri = current_app.config["GOOGLE_REDIRECT_URI"]
    return google.authorize_redirect(redirect_uri)


@auth_bp.route("/auth/callback")
def auth_callback():
    """Handle Google OAuth callback: exchange code for token, set session."""
    try:
        oauth = current_app.extensions["authlib.integrations.flask_client"]
        google = oauth.google
        token = google.authorize_access_token()

        # Try to get user info from id_token first, fall back to userinfo endpoint
        user_info = token.get("userinfo")
        if not user_info:
            user_info = google.userinfo()

        # Set Flask session
        session["user_id"] = user_info["sub"]
        session["user_name"] = user_info.get("name", "User")
        session["user_email"] = user_info.get("email", "")
        session["user_pic"] = user_info.get("picture", "")
        session["logged_in"] = True

        # Save/update user in MongoDB
        from utils.db_service import upsert_user

        db = current_app.config["DB"]
        upsert_user(db, user_info)

        return redirect(url_for("pages.dashboard"))

    except Exception as e:
        print(f"OAuth callback error: {e}")
        return redirect("/?error=auth_failed")


@auth_bp.route("/logout")
def logout():
    """Clear session and redirect to landing page."""
    session.clear()
    return redirect(url_for("pages.landing"))

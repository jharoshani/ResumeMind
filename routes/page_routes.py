from flask import Blueprint, render_template, session, redirect, url_for, request

page_bp = Blueprint("pages", __name__)


@page_bp.route("/")
def landing():
    """Landing page — shows login or redirects to dashboard if logged in."""
    if session.get("logged_in"):
        return redirect(url_for("pages.dashboard"))
    error = request.args.get("error")
    return render_template("login.html", error=error)


@page_bp.route("/dashboard")
def dashboard():
    """Main analysis dashboard — protected route."""
    if not session.get("logged_in"):
        return redirect(url_for("pages.landing"))
    return render_template(
        "dashboard.html",
        user_name=session.get("user_name", "User"),
        user_email=session.get("user_email", ""),
        user_pic=session.get("user_pic", ""),
    )


@page_bp.route("/history")
def history_page():
    """Analysis history page — protected route."""
    if not session.get("logged_in"):
        return redirect(url_for("pages.landing"))
    return render_template(
        "history.html",
        user_name=session.get("user_name", "User"),
        user_pic=session.get("user_pic", ""),
    )

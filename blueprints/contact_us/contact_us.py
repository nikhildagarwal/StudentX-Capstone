from flask import Blueprint, render_template, redirect, url_for, session, request
from firebase_admin import db

contact_us_bp = Blueprint("contact_us", __name__, template_folder="templates")


@contact_us_bp.route("/contact")
def contact():
    logged = session.get('uid', None) is not None
    if session.get("from_contact", False):
        session["from_contact"] = False
        return render_template(
            "./contact_us.html",
            message="Thank you for contacting us! We will get back to you soon.",
            error_message="", logged_in=logged
        )
    return render_template("./contact_us.html", logged_in=logged)

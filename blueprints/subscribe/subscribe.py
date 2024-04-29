from flask import Blueprint, render_template, redirect, url_for, session, request
from firebase_admin import db, storage
import time

subscribe_bp = Blueprint("subscribe", __name__, template_folder="templates")


def convert_email(email):
    """
    Converts a given email into a hashable key in firebase db
    :param email: user given email
    :return: unique netID
    """
    netID = email.split("@")[0]
    result = ""
    for char in netID:
        if char in {'.', '_', '-'}:
            result += '+'
        else:
            result += char
    return result


@subscribe_bp.route('/subscribe/<key>/<email>')
def subscribe(key, email):
    if key == "welcome":
        return render_template('./subscribe.html', message=f"Thank you for subscribing {email}!")
    elif key == "return":
        return render_template('./subscribe.html', message=f"You are already subscribed {email}!")
    

@subscribe_bp.route('/api/subscribe/<email>', methods=['POST'])
def api_subscribe(email):
    converted_email = convert_email(email)
    output = db.reference(f'subscribers/{converted_email}').get()
    uid = db.reference(f'active/{converted_email}').get()
    if output is None:
        db.reference(f'subscribers/{converted_email}').set({'email': email, 'uid':str(uid)})
        return "added"
    else:
        db.reference(f'subscribers/{converted_email}').update({'email': email, 'uid':str(uid)})
        return "return"
    

@subscribe_bp.route('/api/subscribe/delete/<email>', methods=['POST'])
def api_subscribe_delete(email):
    converted_email = convert_email(email)
    db.reference(f'subscribers/{converted_email}').delete()
    return "deleted"
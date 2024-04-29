import os, firebase_admin, uuid, time

from flask import Flask, render_template, redirect, url_for, session, request
from jinja2 import Environment
from firebase_admin import credentials, db, storage, initialize_app
from scripts.user import (
    create_user,
    check_user_exists,
    check_pending_user_exists,
    delete_user,
)
from scripts.security import (
    check_valid,
    passwords,
    check_valid_password,
    check_rutgers_email,
)
from scripts.mail import mail
from flask_socketio import SocketIO, join_room, leave_room, send
from blueprints.chat.chat import chat_bp, rooms_tracker_chat, room_tracker_KEYS
from datetime import timedelta
from flask_cors import CORS
from blueprints.profile.profile import profile_bp
from blueprints.store.store import store_bp, HOLDER
from blueprints.contact_us.contact_us import contact_us_bp
from blueprints.subscribe.subscribe import subscribe_bp
from blueprints.item.item import item_bp
from blueprints.basket.basket import basket_bp
from blueprints.faq.faq import faq_bp
from blueprints.questionaire.questionaire import questionaire_bp
from dotenv import load_dotenv

"""
DO NOT TOUCH : START
"""
load_dotenv()


def create_app():
    new_app = Flask(__name__, template_folder="html")
    new_app.register_blueprint(profile_bp)
    new_app.register_blueprint(chat_bp)
    new_app.register_blueprint(store_bp)
    new_app.register_blueprint(contact_us_bp)
    new_app.register_blueprint(subscribe_bp)
    new_app.register_blueprint(item_bp)
    new_app.register_blueprint(faq_bp)
    new_app.register_blueprint(basket_bp)
    new_app.register_blueprint(questionaire_bp)
    return new_app


app = create_app()
app.jinja_env.globals.update(len=len, str=str)
CORS(app)
app.config["DEBUG"] = os.environ.get("FLASK_DEBUG")
app.config["CATEGORIES"] = [
    "Tech",
    "Clothing",
    "Books",
    "Home_Decor",
    "Lighting",
    "Furniture",
    "Appliances",
    "Other",
]
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=15)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
app.config["DB_URL"] = os.environ.get("DB_URL")
app.config["FIREBASE_KEY_PATH"] = os.environ.get("FIREBASE_KEY_PATH")
app.config["TO_ALL"] = os.environ.get("TO_ALL")
app.config["TO_TECH"] = os.environ.get("TO_TECH")
app.config["TO_CLOTHING"] = os.environ.get("TO_CLOTHING")
app.config["TO_BOOKS"] = os.environ.get("TO_BOOKS")
app.config["TO_HOME_DECOR"] = os.environ.get("TO_HOME_DECOR")
app.config["TO_LIGHTING"] = os.environ.get("TO_LIGHTING")
app.config["TO_FURNITURE"] = os.environ.get("TO_FURNITURE")
app.config["TO_APPLIANCES"] = os.environ.get("TO_APPLIANCES")
app.config["TO_OTHER"] = os.environ.get("TO_OTHER")
app.config["TO_FAQ"] = os.environ.get("TO_FAQ")
app.config["TO_ABOUT"] = os.environ.get("TO_ABOUT")
app.config["TO_CONTACT"] = os.environ.get("TO_CONTACT")
app.config["TO_HOUSING"] = os.environ.get("TO_HOUSING")
app.config["TO_PARKING"] = os.environ.get("TO_PARKING")
app.config["TO_SURVEY"] = os.environ.get("TO_SURVEY")
app.config["TO_CHAT"] = os.environ.get("TO_CHAT")
app.config["TO_MYITEMS"] = os.environ.get("TO_MYITEMS")
app.config["TO_CART"] = os.environ.get("TO_CART")
app.config["TO_PROFILE"] = os.environ.get("TO_PROFILE")
app.config["TO_REC"] = os.environ.get("TO_REC")
app.config["VALID_ROUTES"] = {
    app.config["TO_ALL"],
    app.config["TO_TECH"],
    app.config["TO_CLOTHING"],
    app.config["TO_BOOKS"],
    app.config["TO_HOME_DECOR"],
    app.config["TO_LIGHTING"],
    app.config["TO_FURNITURE"],
    app.config["TO_APPLIANCES"],
    app.config["TO_OTHER"],
    app.config["TO_FAQ"],
    app.config["TO_CONTACT"],
    app.config["TO_ABOUT"],
    app.config["TO_HOUSING"],
    app.config["TO_PARKING"],
    app.config["TO_SURVEY"],
    app.config["TO_CHAT"],
    app.config["TO_MYITEMS"],
    app.config["TO_CART"],
    app.config["TO_PROFILE"],
    app.config["TO_REC"]
}
cred = credentials.Certificate(app.config["FIREBASE_KEY_PATH"])
firebase_admin.initialize_app(
    cred,
    {
        "databaseURL": app.config["DB_URL"],
        "storageBucket": os.environ.get("FIREBASE_STORAGE_BUCKET"),
    },
)
app.config["DB_CONNECTION"] = db.reference("")
socketio = SocketIO(app)
"""
DO NOT TOUCH : END
"""


@app.route("/verify/<uid>/<routing_key>", methods=["POST", "DELETE"])
def api_verification_new_user_routing(uid, routing_key):
    try:
        verification_code = int(request.form.get("code"))
        if verification_code is None:
            return render_template("verify_route.html", uid=uid, routing_key=routing_key, error_message="please enter a verification code")
        code_ref = db.reference(f"codes/{uid}")
        code = str(code_ref.child("code").get())
        timestamp = code_ref.child("timestamp").get()
        if timestamp is None:
            db.reference(f"codes/{uid}").delete()
            return render_template(
                "./verify_route.html", uid=uid, error_message="Code Expired", routing_key=routing_key
            )
        timestamp2 = time.time()
        time_diff = timestamp2 - float(timestamp)
        if time_diff > 180:
            db.reference(f"codes/{uid}").delete()
            return render_template(
                "./verify_route.html", uid=uid, error_message="Code Expired", routing_key=routing_key
            )
        if code is None:
            db.reference(f"codes/{uid}").delete()
            return render_template(
                "./verify_route.html", uid=uid, error_message="Invalid Code", routing_key=routing_key
            )
        if str(verification_code) != code:
            return render_template(
                "./verify_route.html", uid=uid, error_message="Invalid Code", routing_key=routing_key
            )
        data_ref = db.reference(f"codes/{uid}/meta")
        data = data_ref.get()
        if data is None:
            db.reference(f"codes/{uid}").delete()
            return render_template(
                "./verify_route.html", uid=uid, error_message="Invalid Code", routing_key=routing_key
            )
        cu = create_user.CreateUser(db.reference(""), data, uid)
        if cu.response == 200:
            name_ref = db.reference(f"codes/{uid}/meta")
            first_name = name_ref.child("first_name").get()
            last_name = name_ref.child("last_name").get()
            email = name_ref.child("email").get()
            session["first_name"] = first_name
            session["last_name"] = last_name
            session["email"] = email
            db.reference(f"codes/{uid}").delete()
            db.reference(f"pending/{uid}").delete()
            session["uid"] = uid
            if HOLDER.get(session['uid'], None) is not None:
                del HOLDER[session['uid']]
            if routing_key in app.config["VALID_ROUTES"]:
                session["allow_routing"] = True
                return redirect(url_for("route", routing_key=routing_key))
            else:
                return redirect(
                    url_for("home")
                )  # redirect to home logged in (invalid routing key)
        return cu.response  # error message
    except Exception as e:
        return str(e)


@app.route("/verify/<uid>", methods=["POST", "DELETE"])
def api_verification_new_user(uid):
    try:
        verification_code = int(request.form.get("code"))
        if verification_code is None:
            return render_template("verify.html", uid=uid, error_message="please enter a verification code")
        code_ref = db.reference(f"codes/{uid}")
        code = str(code_ref.child("code").get())
        timestamp = code_ref.child("timestamp").get()
        if timestamp is None:
            db.reference(f"codes/{uid}").delete()
            return render_template(
                "./verify.html", uid=uid, error_message="Code Expired"
            )
        timestamp2 = time.time()
        time_diff = timestamp2 - float(timestamp)
        if time_diff > 180:
            db.reference(f"codes/{uid}").delete()
            return render_template(
                "./verify.html", uid=uid, error_message="Code Expired"
            )
        if code is None:
            db.reference(f"codes/{uid}").delete()
            return render_template(
                "./verify.html", uid=uid, error_message="Invalid Code"
            )
        if str(verification_code) != code:
            return render_template(
                "./verify.html", uid=uid, error_message="Invalid Code"
            )
        data_ref = db.reference(f"codes/{uid}/meta")
        data = data_ref.get()
        if data is None:
            db.reference(f"codes/{uid}").delete()
            return render_template(
                "./verify.html", uid=uid, error_message="Invalid Code"
            )
        cu = create_user.CreateUser(db.reference(""), data, uid)
        if cu.response == 200:
            name_ref = db.reference(f"codes/{uid}/meta")
            first_name = name_ref.child("first_name").get()
            last_name = name_ref.child("last_name").get()
            email = name_ref.child("email").get()
            session["first_name"] = first_name
            session["last_name"] = last_name
            session["email"] = email
            db.reference(f"codes/{uid}").delete()
            db.reference(f"pending/{uid}").delete()
            session["uid"] = uid
            return redirect(url_for("home"))
        return cu.response  # error message
    except Exception as e:
        return str(e)


@app.route("/verify/<uid>")
def verify(uid):
    return render_template("./verify.html", uid=uid)


@app.route("/verify/<uid>/<routing_key>")
def verify_route(uid, routing_key):
    return render_template("./verify_route.html", uid=uid, routing_key=routing_key)


@app.route("/signup/<routing_key>", methods=["POST"])
def api_create_user_routing(routing_key):
    connection = app.config["DB_CONNECTION"]
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    email = request.form.get("email")
    terms = request.form.get("terms")
    password1 = request.form.get("password1")
    password2 = request.form.get("password2")
    if str(terms) == "None":
        return render_template(
            "./signup_route.html",
            error_message="please accept our Terms of Service and Privacy Policy",
            EMAIL=email,
            FIRST_NAME=first_name,
            LAST_NAME=last_name,
            PASSWORD1=password1,
            PASSWORD2=password2,
            routing_key = routing_key
        )
    cv = check_valid.CheckValid(password1, password2)
    if cv.error_message is not None:
        return render_template(
            "./signup_route.html",
            error_message=cv.error_message,
            FIRST_NAME=first_name,
            LAST_NAME=last_name,
            EMAIL=email,
            routing_key=routing_key
        )
    cru = check_rutgers_email.CheckRutgersEmail(email)
    if cru.error_message is not None:
        return render_template('./signup_route.html', error_message=cru.error_message,
                               FIRST_NAME=first_name, LAST_NAME=last_name, PASSWORD1=password1, PASSWORD2=password2, routing_key=routing_key)
    cue = check_user_exists.CheckUserExists(connection, email)
    password = passwords.encrypt_password(password1)
    uid = str(uuid.uuid4())
    if cue.response == 302:
        cpue = check_pending_user_exists.CheckPendingUserExists(connection, email)
        if cpue.uid is not None:
            uid = cpue.uid
        SM = mail.Mailer(app)
        res = SM.send_verification_code(
            "studentx.app.group@gmail.com",
            [email],
            {
                "first_name": first_name,
                "last_name": last_name,
                "password": password,
                "uid": uid,
                "email": email,
            },
            uid,
        )
        if res == 200:
            return redirect(url_for("verify_route", uid=uid, routing_key=routing_key)) #TO VERIFICATION CODE
        return res
    elif cue.response == 301:
        return render_template(
            "./signup_route.html",
            error_message="Email is already associated with another account",
            EMAIL=email,
            FIRST_NAME=first_name,
            LAST_NAME=last_name,
            PASSWORD1=password1,
            PASSWORD2=password2,
            routing_key=routing_key
        )
    else:
        return str(cue.response)


@app.route("/signup", methods=["POST"])
def api_create_user():
    connection = app.config["DB_CONNECTION"]
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    email = request.form.get("email")
    terms = request.form.get("terms")
    password1 = request.form.get("password1")
    password2 = request.form.get("password2")
    if str(terms) == "None":
        return render_template(
            "./signup.html",
            error_message="please accept our Terms of Service and Privacy Policy",
            EMAIL=email,
            FIRST_NAME=first_name,
            LAST_NAME=last_name,
            PASSWORD1=password1,
            PASSWORD2=password2,
        )
    cv = check_valid.CheckValid(password1, password2)
    if cv.error_message is not None:
        return render_template(
            "./signup.html",
            error_message=cv.error_message,
            FIRST_NAME=first_name,
            LAST_NAME=last_name,
            EMAIL=email,
        )
    cru = check_rutgers_email.CheckRutgersEmail(email)
    if cru.error_message is not None:
        return render_template('./signup.html', error_message=cru.error_message,
                               FIRST_NAME=first_name, LAST_NAME=last_name, PASSWORD1=password1, PASSWORD2=password2)
    cue = check_user_exists.CheckUserExists(connection, email)
    password = passwords.encrypt_password(password1)
    uid = str(uuid.uuid4())
    if cue.response == 302:
        cpue = check_pending_user_exists.CheckPendingUserExists(connection, email)
        if cpue.uid is not None:
            uid = cpue.uid
        SM = mail.Mailer(app)
        res = SM.send_verification_code(
            "studentx.app.group@gmail.com",
            [email],
            {
                "first_name": first_name,
                "last_name": last_name,
                "password": password,
                "uid": uid,
                "email": email,
            },
            uid,
        )
        if res == 200:
            return redirect(url_for("verify", uid=uid)) #TO VERIFICATION CODE
        return res
    elif cue.response == 301:
        return render_template(
            "./signup.html",
            error_message="Email is already associated with another account",
            EMAIL=email,
            FIRST_NAME=first_name,
            LAST_NAME=last_name,
            PASSWORD1=password1,
            PASSWORD2=password2,
        )
    else:
        return str(cue.response)


@app.route("/signup")
def signup():
    session.clear()
    return render_template("./signup.html")

@app.route("/signup/<routing_key>")
def signup_route(routing_key):
    session.clear()
    return render_template("./signup_route.html", routing_key=routing_key)


@app.route("/logout")
def logout():
    if session.get('uid', None) is None:
        return render_template('logout.html')
    if HOLDER.get(session['uid'], None) is not None:
        del HOLDER[session['uid']]
    session.clear()
    return render_template('logout.html')


@app.route("/login/<routing_key>", methods=["POST"])
def api_login_routing(routing_key):
    step = request.form.get("step", None)
    if step is not None:
        if step == "enter_email":
            return render_template(
                "login_route.html", step=step, routing_key=routing_key
            )
        elif step == "got_email":
            email = request.form.get("email")
            converted_email = check_user_exists.convert_email(email)
            uid = db.reference(f"active/{converted_email}").get()
            if uid is None:
                return render_template(
                    "login_route.html",
                    step="enter_email",
                    error_message="email is not associated with any account",
                    routing_key=routing_key,
                )
            else:
                session["password_reset_uid"] = uid
                SM = mail.Mailer(app)
                SM.send_verification_code_password(
                    "studentx.capstone@gmail.com", [email]
                )
                return render_template(
                    "login_route.html", step="enter_code", routing_key=routing_key
                )
        elif step == "got_code":
            code = request.form.get("code")
            if (
                session.get("password_verification_attempts", None) is None
                or session.get("password_verification_code", None) is None
            ):
                session.pop("password_verification_attempts", None)
                session.pop("password_verification_code", None)
                return render_template(
                    "login_route.html",
                    step="enter_code",
                    error_message="Code Invalid",
                    routing_key=routing_key,
                )
            if session.get("password_verification_attempts") > 0:
                if session.get("password_verification_code") == code:
                    session.pop("password_verification_code", None)
                    session.pop("password_verification_attempts", None)
                    return render_template(
                        "login_route.html",
                        step="enter_new_password",
                        routing_key=routing_key,
                    )
                else:
                    session["password_verification_attempts"] -= 1
                    return render_template(
                        "login_route.html",
                        step="enter_code",
                        error_message="Incorrect code",
                        routing_key=routing_key,
                    )
            else:
                return render_template(
                    "login_route.html",
                    step="enter_code",
                    error_message="Too many attempts, code is invalid",
                    routing_key=routing_key,
                )
        elif step == "got_new_password":
            if session.get("password_reset_uid", None) is None:
                return render_template(
                    "login_route.html",
                    step="",
                    error_message="Session expired, please try again",
                    routing_key=routing_key,
                )
            p1 = request.form.get("password1")
            p2 = request.form.get("password2")
            cv = check_valid.CheckValid(p1, p2)
            if cv.error_message is None:
                encrypted_p = passwords.encrypt_password(p1)
                db.reference(f'users/{session["password_reset_uid"]}/password').set(
                    str(encrypted_p)
                )
                return render_template(
                    "login_route.html",
                    step="",
                    success_message="Password reset sucessfully!",
                    routing_key=routing_key,
                )
            else:
                return render_template(
                    "login_route.html",
                    step="enter_new_password",
                    error_message=cv.error_message,
                    routing_key=routing_key,
                )
    email = request.form.get("email")
    password = request.form.get("password")
    cvp = check_valid_password.CheckValidPassword(db, email, password)
    if cvp.response == 200:
        session["uid"] = cvp.uid
        if HOLDER.get(session['uid'], None) is not None:
            del HOLDER[session['uid']]
        session["first_name"] = cvp.first_name
        session["last_name"] = cvp.last_name
        session["email"] = cvp.email
        profile_img = db.reference(f'users/{session["uid"]}/profile_picture').get()
        if profile_img is None:
            session["profile_picture"] = "/static/img/default_profile_picture.png"
        else:
            session["profile_picture"] = profile_img
        if routing_key in app.config["VALID_ROUTES"]:
            session["allow_routing"] = True
            return redirect(url_for("route", routing_key=routing_key))
        else:
            return redirect(
                url_for("home")
            )  # redirect to home logged in (invalid routing key)
    elif cvp.response == 401:
        return render_template(
            "./login_route.html",
            error_message=cvp.error_message,
            EMAIL=email,
            step="",
            routing_key=routing_key,
        )
    else:
        return render_template(
            "./login_route.html",
            error_message=cvp.error_message,
            step="",
            routing_key=routing_key,
        )


@app.route("/login/<routing_key>")
def login_routing(routing_key):
    session.clear()
    return render_template("login_route.html", step="", routing_key=routing_key)


@app.route("/route/<routing_key>")
def route(routing_key):
    if session.get("allow_routing", False):
        session["allow_routing"] = False
        return render_template(
            "route.html",
            routing_key=routing_key,
            to_all=app.config["TO_ALL"],
            to_tech=app.config["TO_TECH"],
            to_clothing=app.config["TO_CLOTHING"],
            to_books=app.config["TO_BOOKS"],
            to_home_decor=app.config["TO_HOME_DECOR"],
            to_lighting=app.config["TO_LIGHTING"],
            to_furniture=app.config["TO_FURNITURE"],
            to_appliances=app.config["TO_APPLIANCES"],
            to_other=app.config["TO_OTHER"],
            to_faq=app.config["TO_FAQ"],
            to_about=app.config["TO_ABOUT"],
            to_contact=app.config["TO_CONTACT"],
            to_housing=app.config["TO_HOUSING"],
            to_parking=app.config["TO_PARKING"],
            to_survey=app.config["TO_SURVEY"],
            to_chat=app.config["TO_CHAT"],
            to_myitems=app.config["TO_MYITEMS"],
            to_cart=app.config["TO_CART"],
            to_profile=app.config["TO_PROFILE"],
            to_rec = app.config["TO_REC"]
        )
    return redirect(url_for("landing_page"))


@app.route("/login", methods=["POST"])
def api_login():
    step = request.form.get("step", None)
    if step is not None:
        if step == "enter_email":
            return render_template("login.html", step=step)
        elif step == "got_email":
            email = request.form.get("email")
            converted_email = check_user_exists.convert_email(email)
            uid = db.reference(f"active/{converted_email}").get()
            if uid is None:
                return render_template(
                    "login.html",
                    step="enter_email",
                    error_message="email is not associated with any account",
                )
            else:
                session["password_reset_uid"] = uid
                SM = mail.Mailer(app)
                SM.send_verification_code_password(
                    "studentx.capstone@gmail.com", [email]
                )
                return render_template("login.html", step="enter_code")
        elif step == "got_code":
            code = request.form.get("code")
            if (
                session.get("password_verification_attempts", None) is None
                or session.get("password_verification_code", None) is None
            ):
                session.pop("password_verification_attempts", None)
                session.pop("password_verification_code", None)
                return render_template(
                    "login.html", step="enter_code", error_message="Code Invalid"
                )
            if session.get("password_verification_attempts") > 0:
                if session.get("password_verification_code") == code:
                    session.pop("password_verification_code", None)
                    session.pop("password_verification_attempts", None)
                    return render_template("login.html", step="enter_new_password")
                else:
                    session["password_verification_attempts"] -= 1
                    return render_template(
                        "login.html", step="enter_code", error_message="Incorrect code"
                    )
            else:
                return render_template(
                    "login.html",
                    step="enter_code",
                    error_message="Too many attempts, code is invalid",
                )
        elif step == "got_new_password":
            if session.get("password_reset_uid", None) is None:
                return render_template(
                    "login.html",
                    step="",
                    error_message="Session expired, please try again",
                )
            p1 = request.form.get("password1")
            p2 = request.form.get("password2")
            cv = check_valid.CheckValid(p1, p2)
            if cv.error_message is None:
                encrypted_p = passwords.encrypt_password(p1)
                db.reference(f'users/{session["password_reset_uid"]}/password').set(
                    str(encrypted_p)
                )
                return render_template(
                    "login.html", step="", success_message="Password reset sucessfully!"
                )
            else:
                return render_template(
                    "login.html",
                    step="enter_new_password",
                    error_message=cv.error_message,
                )
    email = request.form.get("email")
    password = request.form.get("password")
    cvp = check_valid_password.CheckValidPassword(db, email, password)
    if cvp.response == 200:
        session["uid"] = cvp.uid
        if HOLDER.get(session['uid'], None) is not None:
            del HOLDER[session['uid']]
        session["first_name"] = cvp.first_name
        session["last_name"] = cvp.last_name
        session["email"] = cvp.email
        profile_img = db.reference(f'users/{session["uid"]}/profile_picture').get()
        if profile_img is None:
            session["profile_picture"] = "/static/img/default_profile_picture.png"
        else:
            session["profile_picture"] = profile_img
        return redirect(url_for("home"))  # redirect to home logged in
    elif cvp.response == 401:
        return render_template(
            "./login.html", error_message=cvp.error_message, EMAIL=email, step=""
        )
    else:
        return render_template("./login.html", error_message=cvp.error_message, step="")


@app.route("/login")
def login():
    session.clear()
    return render_template("./login.html", step="")


@app.route("/delete/account", methods=["POST"])
def delete_account():
    uid = session["uid"]
    du = delete_user.DeleteUser(db, uid)
    if du.response == 200:
        session.clear()
        return redirect(url_for("landing_page"))
    else:
        return du.error_message


@app.route("/home")
def home():
    try:
        return render_template("./home.html", uid=session["uid"])
    except KeyError:
        return redirect(url_for("landing_page"))


@app.route("/")
def landing_page():
    try:
        uid = session["uid"]
        return redirect(url_for("home"))
    except KeyError:
        session.clear()
        return render_template("./index.html")


@app.route("/contact", methods=["POST"])
def contact_form_response():
    email = request.form.get("email")
    name = request.form.get("name")
    message = request.form.get("message")
    SM = mail.Mailer(app)
    output = SM.send_contact_form(email, name, message)
    if output == 200:
        session["from_contact"] = True
        return redirect(url_for("contact_us.contact"))
    else:
        return redirect(url_for("contact_us.contact"))


@app.route("/about")
def about():
    logged = session.get("uid", None) is not None
    return render_template("./about.html", logged_in=logged)


@socketio.on("connect")
def connect(auth):
    try:
        for chat_id in session["chat_ids"]:
            if chat_id not in rooms_tracker_chat:
                leave_room(chat_id)
                return
            join_room(chat_id)
            rooms_tracker_chat[chat_id]["count"] += 1
    except KeyError:
        return


@socketio.on("disconnect")
def disconnect():
    try:
        to_remove = []
        for chat_id in session["chat_ids"]:
            leave_room(chat_id)
            if chat_id in rooms_tracker_chat:
                rooms_tracker_chat[chat_id]["count"] -= 1
                if rooms_tracker_chat[chat_id]["count"] <= 0:
                    """
                    update db with messages
                    """
                    ref = db.reference(f"chats/{chat_id}/messages")
                    for MESSAGE in rooms_tracker_chat[chat_id]["new_messages"]:
                        ref.push(MESSAGE)
                    if (
                        rooms_tracker_chat[chat_id]["rts"] is not None
                        and rooms_tracker_chat[chat_id]["rm"] is not None
                    ):
                        user1 = db.reference(f"chats/{chat_id}/user1").get()
                        db.reference(f"users/{user1}/chats/{chat_id}").update(
                            {
                                "timestamp": rooms_tracker_chat[chat_id]["rts"],
                                "message": rooms_tracker_chat[chat_id]["rm"],
                                "read": rooms_tracker_chat[chat_id][user1],
                            }
                        )
                        user2 = db.reference(f"chats/{chat_id}/user2").get()
                        db.reference(f"users/{user2}/chats/{chat_id}").update(
                            {
                                "timestamp": rooms_tracker_chat[chat_id]["rts"],
                                "message": rooms_tracker_chat[chat_id]["rm"],
                                "read": rooms_tracker_chat[chat_id][user2],
                            }
                        )
                        if not rooms_tracker_chat[chat_id][user2] and len(rooms_tracker_chat[chat_id]["new_messages"]) > 0:
                            MASTER_MAILER = mail.Mailer(app)
                            user1_info = db.reference(f"users/{user1}").get()
                            user2_info = db.reference(f"users/{user2}").get()
                            receiver_name = user2_info['first_name']
                            sender_name = user1_info['first_name']+" "+user1_info['last_name'][0].upper()+"."
                            receiver_email = user2_info['email']
                            rec_message = rooms_tracker_chat[chat_id]["rm"]
                            MASTER_MAILER.send_email_notification(sender_name, receiver_name, receiver_email, rec_message)
                        elif not rooms_tracker_chat[chat_id][user1] and len(rooms_tracker_chat[chat_id]["new_messages"]) > 0:
                            MASTER_MAILER = mail.Mailer(app)
                            user1_info = db.reference(f"users/{user1}").get()
                            user2_info = db.reference(f"users/{user2}").get()
                            receiver_name = user1_info['first_name']
                            sender_name = user2_info['first_name']+" "+user2_info['last_name'][0].upper()+"."
                            receiver_email = user1_info['email']
                            rec_message = rooms_tracker_chat[chat_id]["rm"]
                            MASTER_MAILER.send_email_notification(sender_name, receiver_name, receiver_email, rec_message)
                    del rooms_tracker_chat[chat_id]
                    to_remove.append(chat_id)
        for chat_id in to_remove:
            session["chat_ids"].remove(chat_id)
        if len(session["chat_ids"]) == 0:
            del session["chat_ids"]
    except KeyError:
        return


@socketio.on("message")
def message(data):
    current = data["chat_id"]
    sender_id = data["sender_id"]
    if current not in rooms_tracker_chat:
        return
    content = {
        "uid": session["uid"],
        "message": data["data"],
        "timestamp": time.time(),
        "chat_id": current,
    }
    send(content, to=current)
    room = rooms_tracker_chat[current]
    room["new_messages"].append(content)
    room["rts"] = content["timestamp"]
    room["rm"] = content["message"]
    room[sender_id] = True
    if room["count"] == 1:
        other_id = None
        for key in room:
            if key not in room_tracker_KEYS and key != session["uid"]:
                other_id = key
        room[other_id] = False


if __name__ == "__main__":
    socketio.run(app, allow_unsafe_werkzeug=True)

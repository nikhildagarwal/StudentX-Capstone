from flask import Blueprint, render_template, redirect, url_for, session, request
from firebase_admin import db, storage
from datetime import datetime, timedelta
import time

questionaire_bp = Blueprint("questionaire", __name__, template_folder="templates")


valid_routes = {"rxDvzI12JKa2gTCmAVM6vv2OvQ4wbkPU", "j5GqURl3hu6jf7AcBIJO1WDps3faiKrV"}


def generate_housing_arr(housing):
    parts = housing.split(":")
    return [float(parts[0]), float(parts[1])]


@questionaire_bp.route("/survey")
def questionaire():
    try:
        uid = session['uid']
        return render_template('questionaire.html')
    except KeyError:
        return redirect(url_for('login_routing', routing_key="nCzh7rZBhOfvKPVidZXEshccMz0mcAYm"))
    

@questionaire_bp.route("/survey", methods=["POST"])
def api_survey():
    try:
        enrollment = float(request.form.get("employment_status"))
        housing = request.form.get("housing")
        if housing is None:
            return redirect(url_for('questionaire'))
        housing_arr = generate_housing_arr(housing)
        year = int(request.form.get("year_level"))
        year_arr = [0, 0, 0, 0, 0, 0, 0]
        year_arr[year] = 1.0
        school = int(request.form.get("school"))
        school_arr = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        school_arr[school] = 1.0
        drive = int(request.form.get("drive"))
        categories = [float(request.form.get("c0", 0)),
                    float(request.form.get("c1", 0)),
                    float(request.form.get("c2", 0)),
                    float(request.form.get("c3", 0)),
                    float(request.form.get("c4", 0)),
                    float(request.form.get("c5", 0)),
                    float(request.form.get("c6", 0)),
                    float(request.form.get("c7", 0)),
                    float(request.form.get("c8", 0)),
                    float(request.form.get("c9", 0))]
        uid = session['uid']
        db.reference(f'users/{uid}/survey').set(1)
        db.reference(f'surveys/{uid}').set({
            'enrollment': enrollment,
            'housing': housing_arr,
            'year': year_arr,
            'school': school_arr,
            'drive': drive,
            'categories': categories
        })
        return redirect(url_for('home')) #route to store or profile page depending on where from
    except Exception as e:
        return redirect(url_for('questionaire.questionaire'))
    


@questionaire_bp.route("/survey/<routing_key>")
def questionaire_route(routing_key):
    try:
        uid = session['uid']
        return render_template('questionaire.html', routing_key=routing_key)
    except KeyError:
        return redirect(url_for('login_routing', routing_key="nCzh7rZBhOfvKPVidZXEshccMz0mcAYm"))


@questionaire_bp.route("/survey/<routing_key>", methods=["POST"])
def api_survey_route(routing_key):
    try:
        enrollment = float(request.form.get("employment_status"))
        housing = request.form.get("housing")
        if housing is None:
            return redirect(url_for('questionaire'))
        housing_arr = generate_housing_arr(housing)
        year = int(request.form.get("year_level"))
        year_arr = [0, 0, 0, 0, 0, 0, 0]
        year_arr[year] = 1.0
        school = int(request.form.get("school"))
        school_arr = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        school_arr[school] = 1.0
        drive = int(request.form.get("drive"))
        categories = [float(request.form.get("c0", 0)),
                    float(request.form.get("c1", 0)),
                    float(request.form.get("c2", 0)),
                    float(request.form.get("c3", 0)),
                    float(request.form.get("c4", 0)),
                    float(request.form.get("c5", 0)),
                    float(request.form.get("c6", 0)),
                    float(request.form.get("c7", 0)),
                    float(request.form.get("c8", 0)),
                    float(request.form.get("c9", 0))]
        uid = session['uid']
        db.reference(f'users/{uid}/survey').set(1)
        db.reference(f'surveys/{uid}').set({
            'enrollment': enrollment,
            'housing': housing_arr,
            'year': year_arr,
            'school': school_arr,
            'drive': drive,
            'categories': categories
        })
        if routing_key in valid_routes:
            session["allow_routing"] = True
            return redirect(url_for("route", routing_key=routing_key))
        return redirect(url_for('home'))
    except Exception as e:
        return redirect(url_for('questionaire.questionaire'))
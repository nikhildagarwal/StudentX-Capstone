from flask import Blueprint, render_template, redirect, url_for, session, request
from firebase_admin import db, storage
from datetime import datetime, timedelta
import time

profile_bp = Blueprint("profile", __name__, template_folder="templates")


def coordinate_to_campus(coordinate):
    if coordinate == [-1,0]:
        return 'Busch'
    elif coordinate == [-0.5,-1]:
        return 'College Avenue'
    elif coordinate == [0,0]:
        return 'Livingston'
    elif coordinate == [1, -2.5]:
        return 'Cook'
    elif coordinate == [0.5,-2.25]:
        return 'Douglas'
    elif coordinate == [-0.75, -1.25]:
        return "Off Campus - College Avenue"
    elif coordinate == [0.5, -1]:
        return "Off Campus - Other"
    elif coordinate == [-1, 0.01]:
        return "Commuter"
    else:
        return "Other"
    

index_to_school = ["School of Arts and Sciences",
                   "School of Engineering",
                   "Rutgers Business School",
                   "Mason Gros School of the Arts",
                   "School of Environmental and Biological Sciences",
                   "Ernest Mario School of Pharmacy",
                   "School of Communication and Information",
                   "School of Social Work",
                   "School of Management and Labor Relations",
                   "Other"]


index_to_year = ["Freshman",
                 "Sophomore",
                 "Junior",
                 "Senior",
                 "Masters",
                 "PhD",
                 "Other"]


index_to_category = ["Technology",
                     "Books",
                     "Housing",
                     "Parking",
                     "Furniture",
                     "Appliances",
                     "Home Decoration",
                     "Lighting",
                     "Clothing",
                     "Miscellaneous"]


@profile_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    try:
        uid = session['uid']
        first_name = session['first_name']
        last_name = session['last_name']
        email = session['email']
        
        if request.method == 'POST':
            image = request.files.get('image')
            image_path = f'profile_pictures/{uid}'
            blob = storage.bucket().blob(image_path)
            blob.upload_from_string(image.read(), content_type=image.content_type)
            blob.make_public()
            image_url = blob.public_url
            user_ref = db.reference(f'users/{uid}')
            user_ref.child('profile_picture').set(image_url)
            session['profile_picture'] = image_url
        profile_picture = session.get('profile_picture')
        survey = db.reference(f'surveys/{uid}').get()
        sf=True
        if survey is None:
            sf = False
        data = {}
        if survey is not None:
            driver = 'no'
            if survey['drive'] == 0:
                driver = 'yes'
            enrollment = 'full-time'
            if survey['enrollment'] == 0:
                enrollment = 'part-time'
            campus = coordinate_to_campus(survey['housing'])
            school = ""
            count = 0
            for num in survey['school']:
                if num == 1:
                    school = index_to_school[count]
                    break
                count += 1
            year = ""
            count = 0
            for num in survey['year']:
                if num == 1:
                    year = index_to_year[count]
                    break
                count += 1
            categories = ""
            count = 0
            for num in survey['categories']:
                if num == 1:
                    categories += (index_to_category[count] + " - ")
                count += 1 
            data = {
                'Campus driver':driver,
                'Enrollment status':enrollment,
                'Housing status': campus,
                'School (Major)': school,
                'Academic year': year,
                'Category Interests': categories[:-2]
            }
        return render_template('profile.html', FIRST_NAME=first_name,
                               LAST_NAME=last_name, EMAIL=email, PROFILE_PICTURE=profile_picture, sf=sf, data=data)
    except KeyError:
        if session.get("uid", None) is None:
            return redirect(url_for('login_routing', routing_key="rxDvzI12JKa2gTCmAVM6vv2OvQ4wbkPU"))
        return redirect(url_for('landing_page'))

@profile_bp.route('/profile/edit/first/name', methods=['POST'])
def profile_edit_first_name():
    # print the body of the request
    print('testing2', request.get_data())
    first_name = request.form.get('first_name')
    uid = session['uid']
    ref = db.reference(f'users/{uid}')
    ref.child('first_name').set(first_name)
    session['first_name'] = first_name
    return redirect(url_for('profile.profile'))

@profile_bp.route('/profile/edit/last/name', methods=['POST'])
def profile_edit_last_name():
    last_name = request.form.get('last_name')
    uid = session['uid']
    ref = db.reference(f'users/{uid}')
    ref.child('last_name').set(last_name)
    session['last_name'] = last_name
    return redirect(url_for('profile.profile'))

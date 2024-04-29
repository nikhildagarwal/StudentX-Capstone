from flask import Blueprint, render_template, redirect, url_for, session, request
from firebase_admin import db
import uuid

chat_bp = Blueprint("chat", __name__, template_folder="templates")

rooms_tracker_chat = {}
room_tracker_KEYS = {'count', 'messages', 'new_messages', 'rts', 'rm'}


def generate_chat_id():
    return str(uuid.uuid4())


@chat_bp.route('/chat')
def chat():
    try:
        uid = session['uid']
        output = chat_api_get_chats()
        if output == "No Chats Found":
            return render_template('chat.html', no_chats=True)
        session['uid_to_name'] = output['uid_to_name']
        session['chat_id_to_uid'] = output['chat_id_to_uid']
        session['chat_ids'] = []
        session['chat_id_to_timestamp'] = output['chat_id_to_timestamp']
        for chat_id in session['chat_id_to_uid']:
            session['chat_ids'].append(chat_id)
            check_room(chat_id)
        return render_template('./chat.html')
    except KeyError:
        if session.get("uid", None) is None:
            return redirect(url_for('login_routing', routing_key="KrLYYkIPabviy6GaQrqjK6RTgWfJMkHh"))
        else:
            return redirect(url_for('landing_page'))
    

@chat_bp.route('/chat/fetch/dictionaries', methods=['GET'])
def chat_fetch_dictionaries():
    try:
        uid = session['uid']
        if session['chat_id_to_uid'] == {}:
            return {'no_chats': True}
        return {'uid_to_name': session['uid_to_name'], 'chat_id_to_uid': session['chat_id_to_uid'], 'my_uid': uid, 'no_chats': False, 'recent': session['chat_id_to_timestamp']}
    except KeyError:
        return redirect(url_for('chat.chat'))
    


def chat_api_get_chats():
    uid = session['uid']
    ref = db.reference(f'users/{uid}/chats')
    chats = ref.get()
    if chats is None:
        return "No Chats Found"
    dictionary = {}
    translator = {uid: session['first_name']}
    for chat_id, timestamp in chats.items():
        user1 = db.reference(f'chats/{chat_id}/user1').get()
        user2 = db.reference(f'chats/{chat_id}/user2').get()
        if user1 != uid:
            dictionary[chat_id] = user1
            translator[user1] = db.reference(f'users/{user1}/first_name').get() + " " + db.reference(f'users/{user1}/last_name').get()[0].upper() + "."
        else:
            dictionary[chat_id] = user2
            translator[user2] = db.reference(f'users/{user2}/first_name').get() + " " + db.reference(f'users/{user2}/last_name').get()[0].upper() + "."
        if chat_id in rooms_tracker_chat:
            server_val = rooms_tracker_chat[chat_id]['rts']
            if server_val is not None and server_val > chats[chat_id]['timestamp']:
                chats[chat_id]['timestamp'] = server_val
                chats[chat_id]['message'] = rooms_tracker_chat[chat_id]['rm']
            chats[chat_id]['read'] = rooms_tracker_chat[chat_id][uid]
    return {'uid_to_name': translator, 'chat_id_to_uid': dictionary, 'my_uid': uid, 'chat_id_to_timestamp': chats}


def check_room(chat_id):
    diction = db.reference(f'chats/{chat_id}').get()
    messages = diction.get('messages', None)
    user1 = diction['user1']
    user2 = diction['user2']
    ru1 = db.reference(f'users/{user1}/chats/{chat_id}/read').get()
    ru2 = db.reference(f'users/{user2}/chats/{chat_id}/read').get()
    if ru1 is None:
        ru1 = True
    if ru2 is None:
        ru2 = True
    if rooms_tracker_chat.get(chat_id, None) is None:
        if messages is None:
            rooms_tracker_chat[chat_id] = {'count': 0,
                                            'messages': None,
                                            'new_messages': [], 
                                            'rts': None, 
                                            'rm': None, 
                                            user1: True, 
                                            user2: True}
        else:
            arr = list(messages.values())
            rooms_tracker_chat[chat_id] = {'count': 0, 
                                           'messages': arr, 
                                           'new_messages': [], 
                                           'rts': arr[-1]['timestamp'], 
                                           'rm': arr[-1]['message'], 
                                           user1: ru1, 
                                           user2: ru2}
    return "done"


@chat_bp.route('/api/get/messages/<chat_id>', methods=['GET'])
def api_get_messages(chat_id):
    try:
        session['current_chat_id'] = chat_id
        return rooms_tracker_chat[session['current_chat_id']]
    except KeyError:
        return redirect(url_for('chat.chat'))


@chat_bp.route('/echat')
def echat():
    return render_template('./echat.html')


@chat_bp.route('/api/chat/update/settings/<key1>/<key2>')
def api_chat_update_settings(key1, key2):
    uid = session['uid']
    chat_settings = {"lock_setting": key1, "time_setting": key2}
    db.reference(f'users/{uid}/chat_settings').update(chat_settings)
    return "done"
    


@chat_bp.route('/api/chat/get/settings')
def api_chat_get_settings():
    uid = session['uid']
    chat_settings = db.reference(f'users/{uid}/chat_settings').get()
    if chat_settings is None:
        return {"time_setting": 0, "lock_setting":0}
    return chat_settings


@chat_bp.route('/api/chat/update/read/<curr_uid>/<val>/<chat_id>', methods=['POST'])
def api_chat_update_read(curr_uid, val, chat_id):
    print(curr_uid,": ", val)
    if val == "true":
        val = True
    else:
        val = False
    rooms_tracker_chat[chat_id][curr_uid] = val
    return "done"
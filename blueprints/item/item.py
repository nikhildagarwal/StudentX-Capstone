from flask import Blueprint, render_template, redirect, url_for, session, request
from firebase_admin import db
import uuid
import time
import datetime

item_bp = Blueprint("item", __name__, template_folder="templates")


RECENT_ITEM_COUNT = 5


num_to_month = {
    1: "Jan",
    2: "Feb",
    3: "Mar",
    4: "Apr",
    5: "May",
    6: "Jun",
    7: "Jul",
    8: "Aug",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Dec",
}


def get_date_from_timestamp(timestamp):
    date_time = datetime.datetime.utcfromtimestamp(timestamp)
    year = date_time.year
    month = date_time.month
    day = date_time.day
    return f"{num_to_month[month]} {day}, {year}"


@item_bp.route("/item/<category>/<item_id>")
def item(category, item_id):
    try:
        uid = session["uid"]
        item_ref = db.reference(f"store/{category}/{item_id}")
        item = item_ref.get()
        if item['seller_id'] == uid:
            return render_template('no_item.html')
        name = db.reference(f'users/{item["seller_id"]}/first_name').get() + " " + db.reference(f'users/{item["seller_id"]}/last_name').get()
        item["impressions"] += 1
        item_ref.update({"impressions": item["impressions"]})
        if len(str(item["cents"])) == 1:
            item["cents"] = str(item["cents"]) + "0"
        recent = db.reference(f'users/{uid}/recent_items').get()
        if recent is None:
            db.reference(f'users/{uid}/recent_items/{item_id+":"+category}').set(time.time())
        else:
            if recent.get(item_id+":"+category, None) is None:
                if len(recent) < RECENT_ITEM_COUNT:
                    recent[item_id+":"+category] = time.time()
                else:
                    min_key = min(recent, key=recent.get)
                    del recent[min_key]
                    recent[item_id+":"+category] = time.time()
                db.reference(f'users/{uid}/recent_items').set(recent)
            else:
                recent[item_id+":"+category] = time.time()
                db.reference(f'users/{uid}/recent_items').update(recent)
        return render_template(
            "./singleItem.html",
            item=item,
            seller_name=name,
            created_date=get_date_from_timestamp(item["created_at"]),
            updated_date=get_date_from_timestamp(item["updated_at"])
        )
    except KeyError:
        return redirect(url_for("landing_page"))


@item_bp.route("/api/message/seller/<seller_id>", methods=["POST"])
def api_message_seller(seller_id):
    uid = session["uid"]
    mix1 = f"{seller_id}-{uid}"
    mix2 = f"{uid}-{seller_id}"
    chat_id = db.reference(f"active_chats/{mix1}").get()
    if chat_id is None:
        chat_id = db.reference(f"active_chats/{mix2}").get()
    if chat_id is None:
        """
        NO CHAT MUST CREATE A NEW ONE
        """
        chat_id = str(uuid.uuid4())
        setter = {
            "timestamp": time.time(),
            "message": "Start a conversation",
            "read": False,
        }
        ref = db.reference(f"users/{seller_id}/chats/{chat_id}")
        ref.set(setter)
        ref = db.reference(f"users/{uid}/chats/{chat_id}")
        ref.set(setter)
        ref = db.reference(f"chats/{chat_id}")
        ref.set({"user1": seller_id, "user2": uid})
        db.reference(f"active_chats/{mix1}").set(chat_id)
    return redirect(url_for("chat.chat"))


@item_bp.route("/api/check/cart/<item_id>/<item_category>", methods=["GET"])
def api_check_cart(item_id, item_category):
    value = db.reference(f'users/{session["uid"]}/cart/{item_category}/{item_id}').get()
    if value == 1:
        return "True"
    else:
        return "False"

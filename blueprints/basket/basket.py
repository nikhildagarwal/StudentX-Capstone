from flask import Blueprint, render_template, redirect, url_for, session, request
from firebase_admin import db
import uuid
import time
import datetime

basket_bp = Blueprint("basket", __name__, template_folder="templates")


@basket_bp.route("/api/add/item/cart/<item_id>/<item_category>", methods=["POST"])
def api_add_item_cart(item_id, item_category):
    if "uid" not in session:
        return redirect(url_for("landing_page"))
    cart_item_ref = db.reference(
        f"users/{session['uid']}/cart/{item_category}/{item_id}"
    )
    if cart_item_ref.get() is None:
        cart_item_ref.set(1)
        quant_ref = db.reference(f"users/{session['uid']}/cart_quantity")
        curr_quant = quant_ref.get()
        if curr_quant is None:
            quant_ref.set(1)
        else:
            quant_ref.set(curr_quant + 1)
        return redirect(url_for("basket.basket"))
    return redirect(url_for("basket.basket"))


@basket_bp.route("/api/delete/item/cart/<item_id>/<item_category>", methods=["POST"])
def api_delete_item_cart(item_id, item_category):
    cart_item_ref = db.reference(
        f"users/{session['uid']}/cart/{item_category}/{item_id}"
    )
    cart_item_ref.delete()
    quant_ref = db.reference(f"users/{session['uid']}/cart_quantity")
    curr_quant = quant_ref.get()
    if curr_quant == 1:
        quant_ref.delete()
    else:
        quant_ref.set(curr_quant - 1)
    return redirect(url_for("basket.basket"))


@basket_bp.route("/api/add/item/fav/<item_id>/<item_category>", methods=["POST"])
def api_add_item_fav(item_id, item_category):
    fav_item_ref = db.reference(f"users/{session['uid']}/fav/{item_category}/{item_id}")
    fav_item_ref.set(1)
    return redirect(url_for("store.store"))


@basket_bp.route("/api/delete/item/fav/<item_id>/<item_category>", methods=["POST"])
def api_delete_item_fav(item_id, item_category):
    fav_item_ref = db.reference(f"users/{session['uid']}/fav/{item_category}/{item_id}")
    fav_item_ref.delete()
    return redirect(url_for("store.store"))


@basket_bp.route("/cart")
def basket():
    try:
        uid = session["uid"]
        cart = db.reference(f"users/{uid}/cart").get()
        if cart is None:
            return render_template(
                "basket.html", items=[], message="Cart is Empty", total_price="$0.00"
            )
        items = []
        price = 0.0
        message = ""
        for category in cart:
            ids = cart[category]
            for id in ids:
                curr_item = db.reference(f"store/{category}/{id}").get()
                if curr_item is None:
                    message = "Looks like someone purchased an item(s) before you :("
                    db.reference(
                        f"users/{session['uid']}/cart/{category}/{id}"
                    ).delete()
                    cqr = db.reference(f"users/{session['uid']}/cart_quantity")
                    cart_val = int(cqr.get())
                    cart_val -= 1
                    if cart_val == 0:
                        cqr.delete()
                    else:
                        cqr.set(cart_val)
                else:
                    curr_price = float(
                        str(curr_item["dollars"]) + "." + str(curr_item["cents"])
                    )
                    price += curr_price
                    if len(str(curr_item["cents"])) == 1:
                        curr_item["cents"] = str(curr_item["cents"]) + "0"
                    items.append(curr_item)
        price = "$" + str(round(price, 2))
        parts = price.split(".")
        if len(parts[1]) == 1:
            price = price + "0"
        fav = {}
        fa = db.reference(f'users/{uid}/fav').get()
        if fa is not None:
            for category in fa:
                fav.update(fa[category])
        return render_template(
            "basket.html", items=items, message=message, total_price=price, fav=fav
        )
    except KeyError:
        if session.get("uid", None) is None:
            return redirect(url_for('login_routing', routing_key="g9AXxQqSEigRqKMF8QinTk4tth29M3ap"))
        return redirect(url_for('landing_page'))


@basket_bp.route("/api/check/cart/quantity", methods=["GET"])
def api_check_cart_quantity():
    if "uid" not in session:
        return "0"
    quant_ref = db.reference(f"users/{session['uid']}/cart_quantity")
    curr_quant = quant_ref.get()
    if curr_quant is None:
        return "0"
    else:
        return str(curr_quant)

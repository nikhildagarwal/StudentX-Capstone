from flask import Blueprint, render_template, redirect, url_for, session, request
from firebase_admin import db, storage
import time
import uuid
from transformers import AutoTokenizer, AutoModel
import torch
from sklearn.metrics.pairwise import cosine_similarity
from threading import Thread
import pickle
from scripts.ml_rec.user_matrix import user_matrix_distance
import numpy as np
import random

store_bp = Blueprint("store", __name__, template_folder="templates")
category_to_name = {'appliances': "appliances",
                    'books': "books and school",
                    'clothing': "clothing",
                    'furniture': "furniture",
                    'home_decor': "home decoration",
                    'lighting': "lighting",
                    'other': "other or miscellaneous",
                    'tech': "technology",
                    'parking': "car parking",
                    'housing': "housing & living"}

def load_model():
    try:
        global MODEL
        if MODEL is None:
            with open('semantic_search_model.pkl', 'rb') as f:
                MODEL = pickle.load(f)
    except Exception as e:
        print(e)

def load_tokenizer():
    try:
        global TOKENIZER
        if TOKENIZER is None:
            with open('semantic_search_tokenizer.pkl', 'rb') as f:
                TOKENIZER = pickle.load(f)
    except Exception as e:
        print(e)

def load_fix_spelling_pipeline():
    try:
        global FIX_SPELLING
        with open('spelling_correction_pipeline.pkl', 'rb') as f:
            FIX_SPELLING = pickle.load(f)
    except Exception as e:
        print(e)

TOKENIZER = None
MODEL = None
FIX_SPELLING = None
thread1 = Thread(target=load_tokenizer)
thread1.start()
thread2 = Thread(target=load_model)
thread2.start()
thread3 = Thread(target=load_fix_spelling_pipeline)
thread3.start()


def sentence_transformer_search(search_name, items):
    dict_list = []
    titles = []
    for item_id, item in items.items():
        dict_list.append([item_id, item])
        titles.append(item['title'] + f" in {category_to_name[item['category']]}")
    titles.insert(0, search_name)
    tokens = {'input_ids': [], 'attention_mask': []}
    for title in titles:
        new_tokens = TOKENIZER.encode_plus(title, max_length=74, truncation=True, padding='max_length', return_tensors='pt')
        tokens['input_ids'].append(new_tokens['input_ids'][0])
        tokens['attention_mask'].append(new_tokens['attention_mask'][0])
    titles.pop(0)
    tokens['input_ids'] = torch.stack(tokens['input_ids'])
    tokens['attention_mask'] = torch.stack(tokens['attention_mask'])
    outputs = MODEL(**tokens)
    embeddings = outputs.last_hidden_state
    attention = tokens['attention_mask']
    mask = attention.unsqueeze(-1).expand(embeddings.shape).float()
    mask_embeddings = embeddings * mask
    summed = torch.sum(mask_embeddings, 1)
    counts = torch.clamp(mask.sum(1), min=1e-9) #min prevents divide by zero
    mean_pooled = summed / counts
    mean_pooled = mean_pooled.detach().numpy()
    similarity_scores = cosine_similarity([mean_pooled[0]], mean_pooled[1:]).tolist()[0]
    sorted_scores, sorted_items = zip(*sorted(zip(similarity_scores, dict_list), reverse=True))
    return sorted_items


def truncate_two(arr1, arr2, num_of_vals):
    if len(arr1) <= num_of_vals:
        return arr1, arr2
    new_arr1 = []
    new_arr2 = []
    used_indexes = {-1}
    for i in range(num_of_vals):
        random_index = np.random.randint(0, len(arr1))
        if random_index not in used_indexes:
            used_indexes.add(random_index)
            new_arr1[i] = arr1[random_index]
            new_arr2[i] = arr2[random_index]
    return new_arr1, new_arr2


def truncate_one(arr1, num_of_vals):
    if len(arr1) <= num_of_vals:
        return arr1
    return arr1[0:num_of_vals]


def getPrice(dollars, cents):
    total = str(dollars) + "." + str(cents)
    return float(total)


def sort_elements_by(sort_by):
    arr = []
    arr = list(HOLDER[session['uid']]['MASTER_ITEMS'])
    if sort_by == "default":
        return arr
    elif sort_by == "random":
        random.shuffle(arr)
        return arr
    elif sort_by == "recent":
        arr.sort(key=lambda x: x[1]['updated_at'], reverse=True)
        return arr
    elif sort_by == "popular":
        arr.sort(key=lambda x: x[1]['impressions'], reverse=True)
        return arr
    elif sort_by == "az":
        arr.sort(key=lambda x: x[1]['title'])
        return arr
    elif sort_by == "lowhigh":
        arr.sort(key=lambda x: getPrice(x[1]['dollars'], x[1]['cents']))
        return arr
    elif sort_by == "highlow":
        arr.sort(key=lambda x: getPrice(x[1]['dollars'], x[1]['cents']), reverse=True)
        return arr
    else:
        return arr


ITEMS_PER_PAGE = 6
SORT_OPTIONS = [["default", "Default"],
                ["random", "Random"],
                ["recent", "Recent"],
                ["popular", "Popular"],
                ["az", "A to Z"],
                ["lowhigh", "Price: Low to High"],
                ["highlow", "Price: High to Low"]]


HOLDER = {}


@store_bp.route('/api/del/holder', methods=['POST'])
def api_del_holder():
    print("SLDKGJSLKDJGLSKDJHGLSKDJFLSKDJFLSKJDFKSDF")
    if session.get('uid', None) is None:
        return None
    if HOLDER.get(session['uid'], None) is not None:
        del HOLDER[session['uid']]
        return "Done"
    else:
        return None


@store_bp.route('/store', methods=['GET', 'POST'])
def searchItems():
    try:
        uid = session['uid']  # The seller's ID
        title, min_price, max_price, category = '', '', '', ''
        if db.reference('store').get() is None:
            return render_template('no_store.html')
        if request.method == 'POST':
            if request.form.get("sort", None) is not None:
                sort_by = request.form.get("sort")
                HOLDER[uid]['MASTER_ITEMS'] = sort_elements_by(sort_by)
                HOLDER[uid]['SORT_BY'] = sort_by
                if HOLDER[uid]['MASTER_NUM_PAGES'] == 1:
                    return render_template('shop.html', items=HOLDER[uid]['MASTER_ITEMS'], sorted_items=[], search_name=HOLDER[uid]['SEARCH_NAME'], correct_name = HOLDER[uid]['CORRECT_TEXT'], cart=HOLDER[uid]['MASTER_CART'], fav=HOLDER[uid]['MASTER_FAV'], curr_page=1, num_pages=range(HOLDER[uid]['MASTER_NUM_PAGES']), sort_options=SORT_OPTIONS, selected=sort_by)
                else:
                    return render_template('shop.html', items=HOLDER[uid]['MASTER_ITEMS'][0: ITEMS_PER_PAGE], sorted_items=[], search_name=HOLDER[uid]['SEARCH_NAME'], correct_name = HOLDER[uid]['CORRECT_TEXT'], cart=HOLDER[uid]['MASTER_CART'], fav=HOLDER[uid]['MASTER_FAV'], curr_page=1, num_pages=range(HOLDER[uid]['MASTER_NUM_PAGES']), sort_options=SORT_OPTIONS, selected=sort_by)
            if request.form.get("page", None) is not None:
                curr_page = int(request.form.get("page"))
                start = (curr_page - 1) * ITEMS_PER_PAGE
                end = (curr_page) * ITEMS_PER_PAGE
                SELECTED = "default"
                if HOLDER[uid].get('SORT_BY', None) is not None:
                    SELECTED = HOLDER[uid]['SORT_BY']
                if end > HOLDER[uid]['MASTER_ITEMS_LEN']:
                    return render_template('shop.html', items=HOLDER[uid]['MASTER_ITEMS'][start:], sorted_items=[], search_name=HOLDER[uid]['SEARCH_NAME'], correct_name = HOLDER[uid]['CORRECT_TEXT'], cart=HOLDER[uid]['MASTER_CART'], fav=HOLDER[uid]['MASTER_FAV'], curr_page=curr_page, num_pages=range(HOLDER[uid]['MASTER_NUM_PAGES']), sort_options=SORT_OPTIONS, selected=SELECTED)
                else:
                    return render_template('shop.html', items=HOLDER[uid]['MASTER_ITEMS'][start: end], sorted_items=[], search_name=HOLDER[uid]['SEARCH_NAME'], correct_name = HOLDER[uid]['CORRECT_TEXT'], cart=HOLDER[uid]['MASTER_CART'], fav=HOLDER[uid]['MASTER_FAV'], curr_page=curr_page, num_pages=range(HOLDER[uid]['MASTER_NUM_PAGES']), sort_options=SORT_OPTIONS, selected=SELECTED)
            if request.form.get('title') is not None:
                if MODEL is None or TOKENIZER is None:
                    return render_template('shop.html', items=[], sorted_items=[], search_name="loading semantic search ... please try again soon")
                title = request.form.get('title')
                items = {}
                store = db.reference('store').get()
                for category in store:
                    items.update(store[category])
                sorted_items = sentence_transformer_search(title, items)
                cart = db.reference(f'users/{uid}/cart').get()
                cart_dict = {}
                if cart is not None:
                    for category in cart:
                        cart_dict.update(cart[category])
                fav = {}
                fa = db.reference(f'users/{uid}/fav').get()
                if fa is not None:
                    for category in fa:
                        fav.update(fa[category])
                HOLDER[uid]['MASTER_CART'] = cart_dict
                HOLDER[uid]['MASTER_FAV'] = fav
                HOLDER[uid]['SORT_BY'] = None
                HOLDER[uid]['MASTER_ITEMS'] = sorted_items
                HOLDER[uid]['MASTER_ITEMS_LEN'] = len(HOLDER[uid]['MASTER_ITEMS'])
                HOLDER[uid]['MASTER_NUM_PAGES'] = HOLDER[uid]['MASTER_ITEMS_LEN'] / ITEMS_PER_PAGE
                if HOLDER[uid]['MASTER_ITEMS_LEN'] % ITEMS_PER_PAGE != 0:
                    HOLDER[uid]['MASTER_NUM_PAGES'] += 1
                HOLDER[uid]['MASTER_NUM_PAGES'] = int(HOLDER[uid]['MASTER_NUM_PAGES'])
                HOLDER[uid]['SEARCH_NAME']=title
                if HOLDER[uid]['MASTER_NUM_PAGES'] == 1:
                    if FIX_SPELLING is not None:
                        corrected_text = FIX_SPELLING(title, max_length=48)[0].get('generated_text')
                        if title[-1] not in {'.', '?', '!'}:
                            corrected_text = corrected_text[:-1]
                        if corrected_text.upper() != title.upper():
                            HOLDER[uid]['CORRECT_TEXT'] = corrected_text
                            return render_template('shop.html', items = [], sorted_items = sorted_items, search_name=title, cart=cart_dict, fav=fav, correct_name=corrected_text, num_pages = range(HOLDER[uid]['MASTER_NUM_PAGES']), curr_page=1, sort_options=SORT_OPTIONS, selected="default")
                        else:
                            render_template('shop.html', items = [], sorted_items = sorted_items, search_name=title, cart=cart_dict, fav=fav, num_pages = range(HOLDER[uid]['MASTER_NUM_PAGES']), curr_page=1, sort_options=SORT_OPTIONS, selected="default")
                    return render_template('shop.html', items = [], sorted_items = sorted_items, search_name=title, cart=cart_dict, fav=fav, num_pages = range(HOLDER[uid]['MASTER_NUM_PAGES']), curr_page=1, sort_options=SORT_OPTIONS, selected="default")
                else:
                    if FIX_SPELLING is not None:
                        corrected_text = FIX_SPELLING(title, max_length=48)[0].get('generated_text')
                        if title[-1] not in {'.', '?', '!'}:
                            corrected_text = corrected_text[:-1]
                        if corrected_text.upper() != title.upper():
                            HOLDER[uid]['CORRECT_TEXT'] = corrected_text
                            return render_template('shop.html', items = [], sorted_items = sorted_items[0: ITEMS_PER_PAGE], search_name=title, cart=cart_dict, fav=fav, correct_name=corrected_text, num_pages = range(HOLDER[uid]['MASTER_NUM_PAGES']), curr_page=1, sort_options=SORT_OPTIONS, selected="default")
                        else:
                            render_template('shop.html', items = [], sorted_items = sorted_items[0: ITEMS_PER_PAGE], search_name=title, cart=cart_dict, fav=fav, num_pages = range(HOLDER[uid]['MASTER_NUM_PAGES']), curr_page=1, sort_options=SORT_OPTIONS, selected="default")
                    return render_template('shop.html', items = [], sorted_items = sorted_items[0: ITEMS_PER_PAGE], search_name=title, cart=cart_dict, fav=fav, num_pages = range(HOLDER[uid]['MASTER_NUM_PAGES']), curr_page=1, sort_options=SORT_OPTIONS, selected="default")
            if request.form.get('minPrice') is not None:
                min_price = request.form.get('minPrice')
            if  request.form.get('maxPrice') is not None:
                max_price = request.form.get('maxPrice')
            if request.form.get('category') is not None:
                category = request.form.get('category')      
        if category == "fav":
            cart = db.reference(f'users/{uid}/cart').get()
            cart_dict = {}
            if cart is not None:
                for category in cart:
                    cart_dict.update(cart[category])
            fav = {}
            store = db.reference('store').get()
            items = {}
            fa = db.reference(f'users/{uid}/fav').get()
            if fa is not None:
                for category in fa:
                    for id in fa[category]:
                        if store.get(category,{id: None}).get(id) is None:
                            db.reference(f"users/{session['uid']}/fav/{category}/{id}").delete()
                        else:
                            fav[id] = 1
                            items[id] = store[category][id]
            HOLDER[uid]['MASTER_CART'] = cart_dict
            HOLDER[uid]['MASTER_FAV'] = fav
            HOLDER[uid]['MASTER_ITEMS'] = [[key, value] for key, value in items.items()]
            HOLDER[uid]['MASTER_ITEMS_LEN'] = len(HOLDER[uid]['MASTER_ITEMS'])
            HOLDER[uid]['SORT_BY'] = None
            HOLDER[uid]['MASTER_NUM_PAGES'] = HOLDER[uid]['MASTER_ITEMS_LEN'] / ITEMS_PER_PAGE
            if HOLDER[uid]['MASTER_ITEMS_LEN'] % ITEMS_PER_PAGE != 0:
                HOLDER[uid]['MASTER_NUM_PAGES'] += 1
            HOLDER[uid]['MASTER_NUM_PAGES'] = int(HOLDER[uid]['MASTER_NUM_PAGES'])
            HOLDER[uid]['SEARCH_NAME']=None
            HOLDER[uid]['CORRECT_TEXT']=None
            if HOLDER[uid]['MASTER_NUM_PAGES'] == 1:
                return render_template('shop.html', items=HOLDER[uid]['MASTER_ITEMS'], sorted_items=[], cart=cart_dict, fav=fav, num_pages = range(HOLDER[uid]['MASTER_NUM_PAGES']), curr_page=1, sort_options=SORT_OPTIONS, selected="default")
            else:
                return render_template('shop.html', items=HOLDER[uid]['MASTER_ITEMS'][0:ITEMS_PER_PAGE], sorted_items=[], cart=cart_dict, fav=fav, num_pages = range(HOLDER[uid]['MASTER_NUM_PAGES']), curr_page=1, sort_options=SORT_OPTIONS, selected="default")
        elif category == "cart":
            cart = db.reference(f'users/{uid}/cart').get()
            store = db.reference('store').get()
            items = {}
            cart_dict = {}
            if cart is not None:
                for category in cart:
                    for id in cart[category]:
                        try:
                            cart_dict[id] = 1
                            items[id] = store[category][id]
                        except KeyError:
                            db.reference(f"users/{session['uid']}/cart/{category}/{id}").delete()
            fav = {}
            message = ""
            fa = db.reference(f'users/{uid}/fav').get()
            if fa is not None:
                for category in fa:
                    for id in fa[category]:
                        try:
                            fav[id] = fa[category][id]
                        except KeyError:
                            db.reference(f"users/{session['uid']}/fav/{category}/{id}").delete()
            HOLDER[uid]['MASTER_CART'] = cart_dict
            HOLDER[uid]['MASTER_FAV'] = fav
            HOLDER[uid]['SORT_BY'] = None
            HOLDER[uid]['MASTER_ITEMS'] = [[key, value] for key, value in items.items()]
            HOLDER[uid]['MASTER_ITEMS_LEN'] = len(HOLDER[uid]['MASTER_ITEMS'])
            HOLDER[uid]['MASTER_NUM_PAGES'] = HOLDER[uid]['MASTER_ITEMS_LEN'] / ITEMS_PER_PAGE
            if HOLDER[uid]['MASTER_ITEMS_LEN'] % ITEMS_PER_PAGE != 0:
                HOLDER[uid]['MASTER_NUM_PAGES'] += 1
            HOLDER[uid]['MASTER_NUM_PAGES'] = int(HOLDER[uid]['MASTER_NUM_PAGES'])
            HOLDER[uid]['SEARCH_NAME']=message
            HOLDER[uid]['CORRECT_TEXT']=None
            if HOLDER[uid]['MASTER_NUM_PAGES'] == 1:
                return render_template('shop.html', items=HOLDER[uid]['MASTER_ITEMS'], sorted_items=[], cart=cart_dict, fav=fav, search_name=message, num_pages = range(HOLDER[uid]['MASTER_NUM_PAGES']), curr_page=1, sort_options=SORT_OPTIONS, selected="default")
            else:
                return render_template('shop.html', items=HOLDER[uid]['MASTER_ITEMS'][0:ITEMS_PER_PAGE], sorted_items=[], cart=cart_dict, fav=fav, search_name=message, num_pages = range(HOLDER[uid]['MASTER_NUM_PAGES']), curr_page=1, sort_options=SORT_OPTIONS, selected="default")
        elif category == "rec":
            filled_survey = db.reference(f'users/{uid}/survey').get()
            if filled_survey is None:
                return redirect(url_for('questionaire.questionaire_route', routing_key="j5GqURl3hu6jf7AcBIJO1WDps3faiKrV"))
            surveys = db.reference('surveys').get()
            my_survey = surveys.get(session['uid'])
            del surveys[session['uid']]
            uids = list(surveys.keys())
            survs = list(surveys.values())
            uids, survs = truncate_two(uids, survs, 100)
            values = []
            for uid, surv in zip(uids, survs):
                values.append((uid,user_matrix_distance(my_survey, surv)))
            values.sort(key=lambda x: x[1])
            values = truncate_one(values, 10)
            cart = db.reference(f'users/{uid}/cart').get()
            store = db.reference(f'store').get()
            cart_dict = {}
            if cart is not None:
                for category in cart:
                    cart_dict.update(cart[category])
            fav = {}
            fa = db.reference(f'users/{uid}/fav').get()
            if fa is not None:
                for category in fa:
                    fav.update(fa[category])
            items = {}
            for vuid, score in values:
                rv = db.reference(f'users/{vuid}/recent_items').get()
                if rv is not None:
                    for item_id_and_cat in rv:
                        parts = item_id_and_cat.split(":")
                        try:
                            items[parts[0]] = store[parts[1]][parts[0]]
                        except KeyError:
                            pass
            HOLDER[uid]['MASTER_CART'] = cart_dict
            HOLDER[uid]['MASTER_FAV'] = fav
            HOLDER[uid]['SORT_BY'] = None
            HOLDER[uid]['MASTER_ITEMS'] = [[key, value] for key, value in items.items()]
            HOLDER[uid]['MASTER_ITEMS_LEN'] = len(HOLDER[uid]['MASTER_ITEMS'])
            HOLDER[uid]['MASTER_NUM_PAGES'] = HOLDER[uid]['MASTER_ITEMS_LEN'] / ITEMS_PER_PAGE
            if HOLDER[uid]['MASTER_ITEMS_LEN'] % ITEMS_PER_PAGE != 0:
                HOLDER[uid]['MASTER_NUM_PAGES'] += 1
            HOLDER[uid]['MASTER_NUM_PAGES'] = int(HOLDER[uid]['MASTER_NUM_PAGES'])
            HOLDER[uid]['SEARCH_NAME']=None
            HOLDER[uid]['CORRECT_TEXT']=None
            if HOLDER[uid]['MASTER_NUM_PAGES'] == 1:
                return render_template('shop.html', items=HOLDER[uid]['MASTER_ITEMS'], sorted_items=[], cart=cart_dict, fav=fav, search_name="", num_pages = range(HOLDER[uid]['MASTER_NUM_PAGES']), curr_page=1, sort_options=SORT_OPTIONS, selected="default")
            else:
                return render_template('shop.html', items=HOLDER[uid]['MASTER_ITEMS'][0:ITEMS_PER_PAGE], sorted_items=[], cart=cart_dict, fav=fav, search_name="", num_pages = range(HOLDER[uid]['MASTER_NUM_PAGES']), curr_page=1, sort_options=SORT_OPTIONS, selected="default")
        item_ref = db.reference(f'store')
        store = item_ref.get()
        all_items = {}
        for c in store:
            all_items.update(store[c])
        filter_items = {}
        for itemID, item in all_items.items():
            if title != '' and title.lower() not in item['title'].lower():
                continue
            if category != '' and category != 'none' and category.lower() != item['category'].lower():
                continue
            if (min_price != '' and int(min_price) >= int(item['dollars'])):
                continue
            if (max_price != '' and int(max_price) <= int(item['dollars'])):
                continue
            filter_items.update({itemID: item})
        cart = db.reference(f'users/{uid}/cart').get()
        cart_dict = {}
        if cart is not None:
            for category in cart:
                for id in cart[category]:
                    try:
                        cart_dict[id] = cart[category][id]
                    except KeyError:
                        db.reference(f"users/{session['uid']}/cart/{category}/{id}").delete()
        fav = {}
        message = ""
        fa = db.reference(f'users/{uid}/fav').get()
        if fa is not None:
            for category in fa:
                for id in fa[category]:
                    try:
                        fav[id] = fa[category][id]
                    except KeyError:
                        db.reference(f"users/{session['uid']}/fav/{category}/{id}").delete()
        HOLDER[uid] = {}
        HOLDER[uid]['MASTER_FAV'] = fav
        HOLDER[uid]['MASTER_CART'] = cart_dict
        HOLDER[uid]['SORT_BY'] = None
        HOLDER[uid]['MASTER_ITEMS'] = [[key, value] for key, value in filter_items.items()]
        HOLDER[uid]['MASTER_ITEMS_LEN'] = len(HOLDER[uid]['MASTER_ITEMS'])
        HOLDER[uid]['MASTER_NUM_PAGES'] = HOLDER[uid]['MASTER_ITEMS_LEN'] / ITEMS_PER_PAGE
        if HOLDER[uid]['MASTER_ITEMS_LEN'] % ITEMS_PER_PAGE != 0:
            HOLDER[uid]['MASTER_NUM_PAGES'] += 1
        HOLDER[uid]['MASTER_NUM_PAGES'] = int(HOLDER[uid]['MASTER_NUM_PAGES'])
        HOLDER[uid]['SEARCH_NAME']=message
        HOLDER[uid]['CORRECT_TEXT']=None
        if HOLDER[uid]['MASTER_NUM_PAGES'] == 1:
            return render_template('shop.html', items=HOLDER[uid]['MASTER_ITEMS'], sorted_items=[], cart=cart_dict, fav=fav, search_name=message, num_pages = range(HOLDER[uid]['MASTER_NUM_PAGES']), curr_page=1, sort_options=SORT_OPTIONS, selected="default")
        else:
            return render_template('shop.html', items=HOLDER[uid]['MASTER_ITEMS'][0:ITEMS_PER_PAGE], sorted_items=[], cart=cart_dict, fav=fav, search_name=message, num_pages = range(HOLDER[uid]['MASTER_NUM_PAGES']), curr_page=1, sort_options=SORT_OPTIONS, selected="default")
    except Exception as e:
            if session.get("uid", None) is None:
                return redirect(url_for('login_routing', routing_key="dqG724PJ5fCY1Mxx76qpwBROKV6aJe6F"))
            return redirect(url_for('landing_page'))


@store_bp.route('/items', methods=['GET', 'POST'])
def myitems():
    try:
        seller_id = session['uid']  # The seller's ID
        if request.method == 'POST':
            item_id = str(uuid.uuid4())
            title = request.form.get('title')
            price = request.form.get('price-add')
            parts = str(price).split(".")
            dollars = int(parts[0])
            cents = int(parts[1]) if len(parts) > 1 else 0
            category = request.form.get('category')
            image = request.files.get('image')  # Get the image from the form data
            description = request.form.get("item-description")
            # Upload the image to Firebase Storage
            image_path = f'item_images/{seller_id}/{item_id}'
            bucket = storage.bucket()
            blob = bucket.blob(image_path)
            blob.upload_from_string(image.read(), content_type=image.content_type)
            blob.make_public()
            image_url = blob.public_url
            # Create a new marketplace item
            item_data = {
                'title': title,
                'dollars': dollars,
                'cents': cents,
                'category': category,
                'image_url': image_url,  # Add the image URL to the item data
                'created_at': time.time(),
                'updated_at': time.time(),
                'impressions': 0,
                'item_id': item_id,
                'seller_id': seller_id,
                'description': description
            }
            db.reference(f'store/{category}/{item_id}').set(item_data)
            db.reference(f'users/{seller_id}/items/{item_id}').set(category)
        item_ids_to_titles = db.reference(f'users/{seller_id}/items').get()
        if item_ids_to_titles is None:
            items = {}
            return render_template('myitems.html', items=items)
        else:
            items = {}
            for ID in item_ids_to_titles:
                items[ID] = db.reference(f'store/{item_ids_to_titles[ID]}/{ID}').get()
                cents = items[ID]["cents"]
                if len(str(cents)) == 1:
                    cents = str(cents) + "0"
                items[ID]["cents"] = cents
            return render_template('myitems.html', items=items)
    except KeyError:
        if session.get("uid", None) is None:
            return redirect(url_for('login_routing', routing_key="Tk4WgyOVQK6KBUiVrgrZ2SjkVM6NI6Mt"))
        return redirect(url_for('landing_page'))



@store_bp.route('/api/edit/marketplace/item/<item_id>/<category>', methods=['POST'])
def api_edit_marketplace_item(item_id, category):
    title = request.form.get('title')
    price = request.form.get('price')
    parts = str(price).split(".")
    dollars = int(parts[0])
    cents = int(parts[1]) if len(parts) > 1 else 0
    description = request.form.get("item-description")
    if title is None or dollars is None or cents is None or description is None:
        return redirect(url_for('store.myitems'))  # redirect to items page
    item_data = {
        'title': title,
        'dollars': dollars,
        'cents': cents,
        'updated_at': time.time(),
        'description': description
    }
    db.reference(f'store/{category}/{item_id}').update(item_data)
    return redirect(url_for('store.myitems'))  # Redirect to the items page


@store_bp.route('/api/delete/marketplace/item/<item_id>/<category>', methods=['POST'])
def api_delete_marketplace_item(item_id, category):
    seller_id = session['uid']  # The seller's ID
    db.reference(f'users/{seller_id}/items/{item_id}').delete()
    db.reference(f'store/{category}/{item_id}').delete()
    image_path = f'item_images/{seller_id}/{item_id}'
    blob = storage.bucket().blob(image_path)
    blob.delete()
    return "done"


@store_bp.route('/store')
def store():
    try:
        uid = session['uid']
        items = {}
        store = db.reference('store').get()
        if store is None:
            return render_template('no_store.html')
        for category in store:
            items.update(store[category])
        cart = {}
        car = db.reference(f'users/{uid}/cart').get()
        if car is not None:
            for category in car:
                for id in cart[category]:
                    try:
                        cart[id] = cart[category][id]
                    except KeyError:
                        db.reference(f"users/{session['uid']}/cart/{category}/{id}").delete()
        fav = {}
        fa = db.reference(f'users/{uid}/fav').get()
        if fa is not None:
            for category in fa:
                for id in fa[category]:
                    try:
                        fav[id] = fa[category][id]
                    except KeyError:
                        db.reference(f"users/{session['uid']}/fav/{category}/{id}").delete()
        HOLDER[uid] = {}
        HOLDER[uid]['MASTER_CART'] = cart
        HOLDER[uid]['MASTER_FAV'] = fav
        HOLDER[uid]['MASTER_ITEMS'] = [[key, value] for key, value in items.items()]
        HOLDER[uid]['MASTER_ITEMS_LEN'] = len(HOLDER[uid]['MASTER_ITEMS'])
        HOLDER[uid]['MASTER_NUM_PAGES'] = HOLDER[uid]['MASTER_ITEMS_LEN'] / ITEMS_PER_PAGE
        if HOLDER[uid]['MASTER_ITEMS_LEN'] % ITEMS_PER_PAGE != 0:
            HOLDER[uid]['MASTER_NUM_PAGES'] += 1
        HOLDER[uid]['MASTER_NUM_PAGES'] = int(HOLDER[uid]['MASTER_NUM_PAGES'])
        HOLDER[uid]['SEARCH_NAME']=None
        HOLDER[uid]['CORRECT_TEXT']=None
        if HOLDER[uid]['MASTER_NUM_PAGES'] == 1:
            return render_template('shop.html', items=HOLDER[uid]['MASTER_ITEMS'], sorted_items=[], cart=cart, fav=fav, search_name = "", num_pages = range(HOLDER[uid]['MASTER_NUM_PAGES']), curr_page=1, sort_options=SORT_OPTIONS, selected="default")
        else:
            return render_template('shop.html', items=HOLDER[uid]['MASTER_ITEMS'][0: ITEMS_PER_PAGE], sorted_items=[], cart=cart, fav=fav, search_name = "", num_pages = range(HOLDER[uid]['MASTER_NUM_PAGES']), curr_page=1, sort_options=SORT_OPTIONS, selected="default")
    except KeyError:
        if session.get("uid", None) is None:
            return redirect(url_for('login_routing', routing_key="dqG724PJ5fCY1Mxx76qpwBROKV6aJe6F"))
        return redirect(url_for('landing_page'))
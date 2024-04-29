from flask import Blueprint, render_template, redirect, url_for, session, request
from firebase_admin import db, storage
import time
import uuid
from transformers import AutoTokenizer, AutoModel
import torch
from sklearn.metrics.pairwise import cosine_similarity
from threading import Thread
import pickle


class Question:

    def __init__(self, questions_list, answer) -> None:
        self.__questions_list = questions_list
        self.__maxlength = 0
        for question in self.__questions_list:
            if len(question) > self.__maxlength:
                self.__maxlength = len(question)
        self.__answer = answer

    def getQuestions(self):
        return self.__questions_list
    
    def getAnswer(self):
        return self.__answer
    
    def __str__(self) -> str:
        return str(self.__questions_list) + " : " + str(self.__answer)
    
    def getMaxQuestionLength(self):
        return self.__maxlength
    

class QuestionList:

    def __init__(self, questions) -> None:
        self.__questions = questions
        self.__maxlength = 0
        self.__questionCount = 0
        for question in self.__questions:
            self.__questionCount += len(question.getQuestions())
            count = question.getMaxQuestionLength()
            if count > self.__maxlength:
                self.__maxlength = count

    def getMaxQuestionsLength(self):
        return self.__maxlength
    
    def getNumberOfAnswers(self):
        return len(self.__questions)
    
    def getNumberOfQuestions(self):
        return self.__questionCount
    
    def getAllQuestions(self):
        return self.__questions
    


QUESTIONS = QuestionList([
    Question(["Why is my verification code not working?"], 
                "All verification codes terminate after 3 minutes. Please visit the Sign-up page and generate a new code. If you received a code form password-reset, you may have invalidated your code by entering the wrong code too many times. If the issue persists, please contact us on our contact page. Thank You!"),
    Question(["Why is the search bar not working?"], 
                "The search functionality of our store and FAQ page utilizes a Deep Learning NLP Transformer for text embeddings with cosine similarity processing. This enables us to conduct a semantic search. Loading the transformer from hugging-face is quite computationally heavy and can take some time. Please be patient while the model is loading.If the issue persists, please contact us below. Thank You!"),
    Question(["How do I know that the seller is real and can be trusted?"], 
                "All users in the marketplace are verified to be affiliated with Rutgers University. Only Rutgers emails are allowed on this website and all accounts must be verified by verificaiton code prior to store access. Further, seller email information is available to all potential buyers. If you have any additional concerns, please contact us below. Thank You!"),
    Question(["How can I contact the seller about an item?"],
             "Click on the item you want to learn more about and click the 'message seller' button. This will create a chat room between you and the seller. If you run into any issues, please contact us on our contact page. Thank You!"),
    Question(["How do I report an item?"],
             "To report an item, please contact us on the contact page. Thank You!"),
    Question(["How can I post an item to sell?"],
             "First login or create your StudentX account. Then click the + icon in the nav bar (top right of your screen). This will take you to the items page where you can create a new listing for everyone to see! If you run into any issues please contact us on the contact page. Thank you!"),
    Question(["How do I sign up?"],
             "To sign up, you must have a Rutgers email address. To do so, please visit the Sign-up page and fill out the form. A verification code will be sent to your email. If you have any additional concerns, please contact us on the contact page. Thank You!"),
    Question(["How do I reset my password?"],
                "To reset your password, please visit the login page page and click forgot password. We will prompt you for an email and send a verification code to that email. Once we verify your identity you can proceed to enter a new password. If you run into any issues, please contact us on the contact page. Thank you!"),
    Question(["What is the return policy for purchased items"],
             "We do not have a return policy because no transactions are made on our site. Students may post items to sell and the exchange of those items is handled independently between those parties. If you have any further questions please contact us on the contact page. Thank You!"),
    Question(["How do I contact StudentX if I have any issues or questions?"],
                "If you have any questions, or concerns, please contact us on the contact page. Thank You!"),
])

faq_bp = Blueprint("faq", __name__, template_folder="templates")

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

ite = []

allQuestions = QUESTIONS.getAllQuestions()

for Q in allQuestions:
    sqs = Q.getQuestions()
    answer = Q.getAnswer()
    for q in sqs:
        ite.append([q, answer])

def sentence_transformer_search(search_name, items):
    dict_list = []
    titles = []
    for item in items:
        dict_list.append([item[0], item[1]])
        titles.append(item[0])
    titles.insert(0, search_name)
    tokens = {'input_ids': [], 'attention_mask': []}
    for title in titles:
        new_tokens = TOKENIZER.encode_plus(title, max_length=QUESTIONS.getMaxQuestionsLength(), truncation=True, padding='max_length', return_tensors='pt')
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


@faq_bp.route('/faq')
def faq():
    logged = session.get('uid', None) is not None
    return render_template('faq.html', items=ite, search_name="", logged_in=logged)


@faq_bp.route('/faq', methods=['POST'])
def sort_faq():
    logged = session.get('uid', None) is not None
    if MODEL is None or TOKENIZER is None:
        return render_template('faq.html', items=ite, search_name="loading semantic search ... please wait", logged_in=logged)
    ans = sentence_transformer_search(request.form.get('title'), ite)
    text = request.form.get('title')
    if FIX_SPELLING is not None:
        corrected_text = FIX_SPELLING(text, max_length=48)[0].get('generated_text')
        if text[-1] not in {'.', '?', '!'}:
            corrected_text = corrected_text[:-1]
        if corrected_text.upper() != text.upper():
            return render_template('faq.html', items=ans, search_name=text, correct_name=corrected_text, logged_in=logged)
        else:
            return render_template('faq.html', items=ans, search_name=text, logged_in=logged)
    return render_template('faq.html', items=ans, search_name=text, logged_in=logged)
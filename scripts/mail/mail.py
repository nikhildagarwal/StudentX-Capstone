from flask_mail import Mail, Message
import random
import time
from flask import session


class Mailer:

    def __init__(self, app):
        app.config['MAIL_SERVER'] = 'smtp.gmail.com'
        app.config['MAIL_PORT'] = 587
        app.config['MAIL_USE_TLS'] = True
        app.config['MAIL_USE_SSL'] = False
        app.config['MAIL_USERNAME'] = 'studentx.capstone@gmail.com'
        app.config['MAIL_PASSWORD'] = 'suqwsbvrstenfmvw'
        self.mail = Mail(app)
        self.code = ""
        self.email = 'studentx.capstone@gmail.com'
        self.code_ref = app.config['DB_CONNECTION']


    def send_contact_form(self, email, sender_name, message):
        """
        function to send form content of contact page to service email
        """
        msg = Message(f"Contact - {email}", sender=self.email, recipients=[self.email])
        msg.html = (f"Name: {sender_name}<br>" + 
                    f"Email: {email}<br>" +
                    f"Message: {message}")
        self.mail.send(msg)
        return 200
    
    def send_email_notification(self, sender_name, receiver_name, receiver_email, rec_message):
        """
        function to send form content of contact page to service email
        """
        msg = Message(f"New Message - {sender_name}", sender=self.email, recipients=[receiver_email])
        msg.html = (f"Hi {receiver_name},<br><br>" + 
                    f"You have new message(s) from {sender_name}<br><br>" +
                    f"Message: {rec_message}<br><br>" +
                    f"Log into your StudentX account to continue your conversation!<br><br>" + 
                    f"All the Best,<br>StudentX")
        self.mail.send(msg)
        return 200

    def send_verification_code(self, sender, recipients_list, meta_data, uid):
        """
        function to send verification code email to user
        :param sender: string email of sender
        :param recipients_list: list of email strings of recipients
        :param meta_data: dictionary or structured json that can be pushed to the database
        :return:
        """
        try:
            msg = Message("Verification Code", sender=sender, recipients=recipients_list)
            for i in range(6):
                if i == 0 or i == 5:
                    self.code += str(random.randint(1, 9))
                else:
                    self.code += str(random.randint(0, 9))
            msg.html = ("<br>Hi "+ meta_data['first_name'] +"! <br><br>Thanks for signing up. Verify your StudentX account with the following code. "
                        "<br><br>Your 6-digit verification code is: " +
                        "<bold>" + self.code + "</bold>" + "<br><br>All the best,<br>StudentX")
            self.mail.send(msg)
            code_ref = self.code_ref.child('codes')
            p_ref = self.code_ref.child('pending')
            my_dict = {meta_data['uid']: meta_data['email']}
            p_ref.update(
                my_dict
            )
            code_dict = {uid: {"code": str(self.code), "timestamp": time.time(), "meta": meta_data}}
            code_ref.update(code_dict)
            return 200
        except Exception as e:
            return str(e)

    def send_verification_code_password(self, sender, recipients_list):
        """
        function to send verification code email to user
        :param sender: string email of sender
        :param recipients_list: list of email strings of recipients
        :param meta_data: dictionary or structured json that can be pushed to the database
        :return:
        """
        try:
            msg = Message("Verification Code - Password Reset", sender=sender, recipients=recipients_list)
            for i in range(6):
                if i == 0 or i == 5:
                    self.code += str(random.randint(1, 9))
                else:
                    self.code += str(random.randint(0, 9))
            msg.html = ("<br>Hi"+"! <br><br>Looks like you forgot your password. No worries, here is your verification code to reset your password."
                        "<br><br>Your 6-digit verification code is: " +
                        "<bold>" + self.code + "</bold>" + "<br><br>All the best,<br>StudentX")
            self.mail.send(msg)
            session['password_verification_code'] = self.code
            session['password_verification_attempts'] = 5
            return 200
        except Exception as e:
            return str(e)
from scripts.security import passwords


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


def getUID(db, email):
    netID = convert_email(email)
    active_ref = db.reference(f'active/{netID}')
    uid = active_ref.get()
    if uid is None:
        return None
    return uid


class CheckValidPassword:

    def __init__(self, db, email, password):
        """
        Checks if the given password is valid (in that it matches the password of the given email)
        if no account is found for the given email, send 400
        send 400 if password provided does not match as well
        :param db: db connection object
        :param email: string email
        :param password: given password to check against database
        """
        try:
            uid = getUID(db, email)
            if uid is None:
                self.response = 400
                self.error_message = "email is not associated with any account"
            else:
                ref = db.reference(f'users/{uid}')
                retrieved_password = ref.child('password').get()
                first_name = ref.child('first_name').get()
                last_name = ref.child('last_name').get()
                email = ref.child('email').get()
                if passwords.check_passwords_match(password, retrieved_password):
                    self.response = 200
                    self.uid = uid
                    self.first_name = first_name
                    self.last_name = last_name
                    self.email = email
                    self.error_message = None
                else:
                    self.response = 401
                    self.error_message = "Incorrect password"
        except Exception as e:
            self.response = 400
            self.error_message = str(e)

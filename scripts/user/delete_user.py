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


class DeleteUser:

    def __init__(self, db, uid):
        """
        Delete a given account from the database given a uid
        :param db: db connection
        :param uid: user id of the account to delete
        """
        try:
            email = db.reference(f'users/{uid}/email').get()
            active_ref = db.reference(f'active/{convert_email(email)}')
            user_ref = db.reference(f'users/{uid}')
            active_ref.delete()
            user_ref.delete()
            self.response = 200
            self.error_message = None
        except Exception as e:
            self.response = 400
            self.error_message = str(e)

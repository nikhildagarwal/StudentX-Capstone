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


class CheckUserExists:

    # 301 : user exists
    # 302 : user does not exist
    # 400 : error occurred

    def __init__(self, db_ref, email):
        """
        Adds a user to the db
        :param db_ref: connection to the db (passed in from app.py)
        :param email: email
        """
        try:
            converted_email = convert_email(email)
            u_ref = db_ref.child(f'active/{converted_email}')
            data = u_ref.get()
            if data is None:
                self.response = 302
            else:
                self.response = 301
        except Exception as e:
            self.response = e

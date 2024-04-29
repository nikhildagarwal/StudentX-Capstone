import uuid


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


class CreateUser:

    # 200 : user added successfully
    # 400 : error occurred

    def __init__(self, db_ref, meta, uid):
        """
        Adds a user to the db
        :param db_ref: connection to the db (passed in from app.py)
        :param meta: previously stored meta-data in the database
        """
        try:
            u_ref = db_ref.child(f'users/{uid}')
            u_ref.set(meta)
            active_ref = db_ref.child('active')
            my_dict = {convert_email(meta['email']): uid}
            active_ref.update(
                my_dict
            )
            self.response = 200
        except Exception as e:
            self.response = str(e)




class CheckPendingUserExists:

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
            u_ref = db_ref.child('pending')
            data = u_ref.get()
            if data is None:
                self.response = 302
                self.uid = None
            else:
                email_set = False
                for uid, em in data.items():
                    if em == email:
                        self.response = 301
                        self.uid = uid
                        email_set = True
                        break
                if not email_set:
                    self.response = 302
                    self.uid = None
        except Exception as e:
            self.response = e
            self.uid = None

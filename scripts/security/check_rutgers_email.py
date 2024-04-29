class CheckRutgersEmail:

    def __init__(self, email):
        """
        Checks to see if the given email ends in rutgers.edu tag
        :param email: string email
        """
        if email.endswith("rutgers.edu") or email.endswith("scarletmail.rutgers.edu"):
            self.error_message = None
        else:
            self.error_message = "email must be affiliated with Rutgers University"



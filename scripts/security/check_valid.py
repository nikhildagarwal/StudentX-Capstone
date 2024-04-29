class CheckValid:

    def __init__(self, password1, password2):
        """
        Checks to see if the two passwords provided during the signup are valid
        :param password1: first security
        :param password2: confirm security
        """
        self.invalid_characters = []
        if password1 != password2:
            self.error_message = "passwords do not match"
        elif len(password1) < 8:
            self.error_message = "password must be at least 8 characters long"
        else:
            invalid_character = False
            has_uppercase = False
            has_lowercase = False
            has_special = False
            has_number = False
            for c in password1:
                s1 = False
                s2 = False
                s3 = False
                s4 = False
                num = ord(c)
                if num < 33 or num > 126:
                    invalid_character = True
                    s1 = True
                    self.invalid_characters.append(c)
                if 48 <= num <= 57:
                    has_number = True
                    s2 = True
                if 65 <= num <= 90:
                    has_uppercase = True
                    s3 = True
                if 97 <= num <= 122:
                    has_lowercase = True
                    s4 = True
                if not s1 and not s2 and not s3 and not s4:
                    has_special = True
            if invalid_character:
                self.error_message = "the following character(s) are invalid: " + str(self.invalid_characters)
            elif not has_special:
                self.error_message = "password must contain at least one special character"
            elif not has_number:
                self.error_message = "assword must contain at least one number"
            elif not has_uppercase:
                self.error_message = "password must contain at least one upper case letter"
            elif not has_lowercase:
                self.error_message = "password must contain at least one lower case letter"
            else:
                self.error_message = None



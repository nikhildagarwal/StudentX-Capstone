import bcrypt


def encrypt_password(password):
    """
    Encrypts a Given text password
    :param password: string
    :return: hashed password
    """
    salt = bcrypt.gensalt()
    encrypted = bcrypt.hashpw(password.encode('utf-8'), salt)
    return encrypted.decode('utf-8')


def check_passwords_match(given, retrieved):
    """
    Checks to see if the password given and the password stored are the same
    :param given: password given
    :param retrieved: password retrieved from DB
    :return: True if passwords match, False otherwise
    """
    return bcrypt.checkpw(given.encode('utf-8'), retrieved.encode('utf-8'))



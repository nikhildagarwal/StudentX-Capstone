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
    

QUESTIONS = QuestionList([
    Question(["Why won't my verification code work?",
              "Verification code broken?",
                "Why isn't my verification code doing what it should?",
                "What's wrong with my verification code?",
                "Why is my verification code not working?"], 
                "All verification codes terminate after 3 minutes. Please visit the Sign-up page and generate a new code. If the issue persists, please contact us below. Thank You!"),
    Question(["Why is the search bar in the store not working? ",
                "What's the problem with the store's search bar?",
                "Store search bar broken?",
                "Why won't the store's search bar work?",
                "Why isn't the store's search bar functioning?"], 
                "The search functionality of our store utilizes a Deep Learning NLP Transformer for text embeddings and cosine similarity to decipher those embeddings (semantic search). Loading the transformer from hugging-face is quite computationally heavy and can take some time. Please be patient while the model is loading.If the issue persists, please contact us below. Thank You!"),
    Question(["How can I tell if the seller is really a person?",
                "How do I know if I can trust the seller?",
                "Is the seller a real person?",
                "Can I be sure the seller is genuine?",
                "How can I trust that the seller is legit?",
                "How do I know if the seller is trustworthy?"], 
                "All users in the marketplace are verified to be affiliated with Rutgers University. Only Rutgers emails are allowed on this website and all accounts must be verified by verificaiton code prior to store access. Further, seller email information is available to all potential buyers. If you have any additional concerns, please contact us below. Thank You!")
])
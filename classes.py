import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

class DataBase:
    def __init__(self):
        cred = credentials.Certificate('key.json')
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://prezident-selection-default-rtdb.europe-west1.firebasedatabase.app/'
        })
        self.ref = db.reference('/')
        response = self.ref.get()
        self.candidates = response['CandidatesDB']

    def validateCode(self, code):
        response = self.ref.get()
        code_validation = response["ElectionDB"]

        if str(code) not in code_validation:
            return {"status": "error", "message": "Это не код голосования!"}
        elif code_validation[str(code)]["IsValid"] == True:
            return {"status": "error", "message": "Этот код уже был использован!"}

        return {"status": "success"}

    def vote(self, code, candidate):
        self.ref.update({f'ElectionDB/{code}/Chose': candidate})
        self.ref.update({f'ElectionDB/{code}/IsValid': True})

    def clearVote(self, code):
        self.ref.update({f'ElectionDB/{code}/Chose': -1})
        self.ref.update({f'ElectionDB/{code}/IsValid': False})
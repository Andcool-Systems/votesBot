import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage
import os

"""Класс для работы с базой данных"""
class DataBase:
    def __init__(self):
        """Настройка соединения с базой данных"""

        cred = credentials.Certificate('key.json')
        firebase_admin.initialize_app(cred, {
            'databaseURL': os.getenv("URL"),
            'storageBucket': "cand"
        })
        ref = db.reference('/CandidatesDB')
        self.candidates = ref.get()
        bucket = storage.bucket()
        print(self.candidates)


    def validateCode(self, code):
        """Метод проверки кода на валидность"""

        ref = db.reference('/ElectionDB')
        code_validation = ref.get()

        if str(code) not in code_validation:
            return {"status": "error", "message": "Это не код голосования!"}
        elif code_validation[str(code)]["IsValid"]:
            return {"status": "error", "message": "Этот код уже был использован!"}

        return {"status": "success"}


    def vote(self, code, candidate):
        """Метод для обновления данных в бд"""
        ref = db.reference('/ElectionDB')
        ref.update({f'{code}/Chose': candidate})
        ref.update({f'{code}/IsValid': True})

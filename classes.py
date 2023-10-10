import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import os

"""Класс для работы с базой данных"""
class DataBase:
    def __init__(self):
        """Настройка соединения с базой данных"""

        cred = credentials.Certificate('key.json')
        firebase_admin.initialize_app(cred, {
            'databaseURL': os.getenv("URL")
        })
        ref = db.reference('/CandidatesDB')
        self.candidates = ref.get()


    def validateCode(self, code):
        """Метод проверки кода на валидность"""

        ref = db.reference('/ElectionDB')
        code_validation = ref.get()

        if str(code) not in code_validation:
            return {"status": "error", "message": "Это не код голосования!"}
        elif code_validation[str(code)]["IsValid"] == True:
            return {"status": "error", "message": "Этот код уже был использован!"}

        return {"status": "success"}


    def vote(self, code, candidate):
        """Метод для обновления данных в бд"""
        ref = db.reference('/ElectionDB')
        ref.update({f'{code}/Chose': candidate})
        ref.update({f'{code}/IsValid': True})

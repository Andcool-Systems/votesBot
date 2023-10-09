import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

# Инициализация Firebase
cred = credentials.Certificate('key.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://prezident-selection-default-rtdb.europe-west1.firebasedatabase.app/'
})

# Получение ссылки на базу данных
ref = db.reference('/')

# Чтение данных
data = ref.get()

# Вывод данных
print(data)
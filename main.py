from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters.command import Command
from aiogram.types import FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
import os
import json
import requests
import asyncio
from dotenv import load_dotenv

load_dotenv()
bot = Bot(token=os.getenv("TOKEN"))
dp = Dispatcher()

qr_url = "http://api.qrserver.com/v1/read-qr-code/" #url qr апи

class States(StatesGroup):
    candidate = State()
    waiting_to_qr = State()

candidates = [{
                "id": 1,
                "name": "Илья Иванов",
                "info": "15 лет, 89 группа",
                "speech": "Самое главное это учёба!",
                "image": "1.png"
            },
            {
                "id": 2,
                "name": "Федя Фёдоров",
                "info": "16 лет, 76 группа",
                "speech": "Самое главное это спорт!",
                "image": "1.png"
            },
            {
                "id": 3,
                "name": "Катя Спасимирова",
                "info": "15 лет, 91 группа",
                "speech": "Самое главное это животные!",
                "image": "1.png"
            }
]

@dp.message(Command('start'))
async def start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="Приступить к голосованию",
        callback_data="start_voting")
    )
    await message.answer(f"Здравствуйте, {message.from_user.full_name}.\nЯ - бот, созданный для выбора президента лицея в 2023 году.\nДавайте начнём", reply_markup=builder.as_markup())


@dp.callback_query(F.data == "start_voting")
async def send_candidates(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer("Список кандидатов:")

    for candidate in candidates:
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(
            text="Проголосовать",
            callback_data=f"candidate-{candidate['id']}")
        )
        await callback.message.answer_photo(photo=FSInputFile(f"res/1.png"), caption=
                                            f"*{candidate['name']}*\n{candidate['info']}\n\n{candidate['speech']}", parse_mode="Markdown", 
                                            reply_markup=builder.as_markup())
        
    await state.set_state(States.candidate)


@dp.callback_query(F.data.startswith("candidate-"), States.candidate)
async def select_candidate(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(candidate=callback.data.replace("candidate-", ""))


    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
            text="Отмена",
            callback_data="qr_deny")
    )
    await callback.message.answer("Теперь отправьте фото QR кода.\nФото должно быть разборчивым и хорошего качества.", 
                                  reply_markup=builder.as_markup())
    await state.set_state(States.waiting_to_qr)


@dp.callback_query(F.data == "qr_deny")
async def select_candidate(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer("*Отменено*\nЧто бы снова начать процесс голосования отправьте /start", parse_mode="Markdown")


@dp.message(F.photo, States.waiting_to_qr)
async def send_qr(message: types.Message, state: FSMContext):
    candidate = (await state.get_data())["candidate"]

    file_id = message.photo[-1].file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path
    path = "".join(file.file_path.split(".")[-1:])

    await bot.download_file(file_path, f"{message.chat.id}.{path}")

    files = {'file': open(f"{message.chat.id}.{path}", 'rb')} #открываем картинку как массив байт

    response = requests.post(url=qr_url, files=files) #делаем POST запрос к апи, и получаем результат
    data = json.loads(response.content)[0]["symbol"][0]["data"] #Вытаскиваем оттуда значение qr

    print(response.content)
    if response.status_code != 200 or data == None:
        await message.answer("Извините, боту не удалось корректно прочитать QR код.\nПопробуйте сфотографировать чётче")
        return

    await message.answer(f"Дальше что-то там, работа с апи и тд\nДанные qr кода: {data}\nКандидат номер {candidate}")

    files["file"].close()
    await state.clear()
    os.remove(f"{message.chat.id}.{path}")


async def start():
    await dp.start_polling(bot)


if __name__ == '__main__':
    # start bot
    asyncio.run(start())
"""
by AndcoolSystems, 2023
"""

from aiogram import Bot, Dispatcher, types, F
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
import io
from classes import DataBase
import datetime

"""Создание всех нужных объектов"""
load_dotenv()
bot = Bot(token=os.getenv("TOKEN"))
dp = Dispatcher()
db = DataBase()

candidates = db.candidates  # Парсинг данных о кандидатах с бд

qr_url = "http://api.qrserver.com/v1/read-qr-code/"  # url qr апи


class States(StatesGroup):
    """Стейты для aiogram"""

    candidate = State()
    votes_messages = State()
    waiting_to_qr = State()
    final_voting = State()


@dp.message(Command('start'))
async def start(message: types.Message, state: FSMContext):
    """Хэндлер для команды /start"""

    await state.clear()
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="Приступить к голосованию",
        callback_data="start_voting")
    )
    await message.answer(f"Здравствуйте, {message.from_user.full_name}.\nЯ - бот, "
                         + "созданный для выбора президента лицея "
                         + f"в {datetime.datetime.today().year} году.\nДавайте начнём",
                         reply_markup=builder.as_markup())


@dp.callback_query(F.data == "start_voting")
async def send_candidates(callback: types.CallbackQuery, state: FSMContext):
    """Хэндлер для колбэка кнопки 'Приступить к голосованию'"""

    await callback.message.delete()

    votes = [await callback.message.answer("Список кандидатов:")]
    for candidate in candidates:
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(
            text="Проголосовать",
            callback_data=f"candidate-{candidate['Id']}")
        )

        votes.append(await callback.message.answer_photo(
            photo=FSInputFile(f"res/{candidate['Id']}.jpg"),
            caption=f"*{candidate['Name']}*\n{candidate['Age']} лет, {candidate['Group']} группа"
                    + f"\n\n*{candidate['Remarck']}*\n{candidate['ElectionProgramm']}",
            parse_mode="Markdown",
            reply_markup=builder.as_markup()))

    await state.update_data(votes=votes)
    await state.set_state(States.candidate)


@dp.callback_query(F.data.startswith("candidate-"), States.candidate)
async def select_candidate(callback: types.CallbackQuery, state: FSMContext):
    """Хэндлер для колбэка кнопок выбора кандидата"""

    await state.update_data(candidate=callback.data.replace("candidate-", ""))

    votes = (await state.get_data())["votes"]
    for vote in votes:
        try:
            await vote.delete()
        except:
            ...

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="Отмена",
        callback_data="qr_deny")
    )
    await callback.message.answer("Теперь отправьте фото QR кода.\n" +
                                  "Фото должно быть разборчивым и хорошего качества.",
                                  reply_markup=builder.as_markup())
    await state.set_state(States.waiting_to_qr)


@dp.callback_query(F.data == "qr_deny")
async def select_candidate(callback: types.CallbackQuery, state: FSMContext):
    """Хэндлер для колбэка кнопки отмены"""
    await state.clear()
    await callback.message.delete()
    await callback.message.answer("*Отменено*\nЧто бы снова начать процесс голосования отправьте /start",
                                  parse_mode="Markdown")


@dp.message(F.photo, States.waiting_to_qr)
async def send_qr(message: types.Message, state: FSMContext):
    """Хэндлер для фото (qr кода)"""
    candidate = (await state.get_data())["candidate"]

    file_id = message.photo[-1].file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path

    """Скачивание кода как массив байт"""
    bio = io.BytesIO()
    bio.name = f"{message.chat.id}.png"
    photo: io.BytesIO = await bot.download_file(file_path, destination=bio)
    bio.seek(0)
    photo_bytes = photo.read()

    files = {'file': photo_bytes}  # открываем картинку как массив байт
    response = requests.post(url=qr_url, files=files)  # делаем POST запрос к апи, и получаем результат

    data = json.loads(response.content)[0]["symbol"][0]["data"]  # Вытаскиваем оттуда значение qr

    if response.status_code != 200 or data is None:  # Если распознать код не удалось
        await message.answer("Извините, боту не удалось корректно прочитать QR код.\nПопробуйте сфотографировать чётче")
        return

    validation_result = db.validateCode(data)  # Валидация кода
    if validation_result["status"] == "error":
        await message.reply(validation_result["message"])
        return

    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(text="Проголосовать", callback_data="final-Vote"),
        types.InlineKeyboardButton(text="Отмена", callback_data="qr_deny")
    )

    await message.answer(f"Хорошо, вы собираетесь проголосовать за *{candidates[int(candidate)]['Name']}*",
                         parse_mode="Markdown",
                         reply_markup=builder.as_markup())

    await state.update_data(code=data)
    await state.set_state(States.final_voting)


@dp.callback_query(F.data == "final-Vote", States.final_voting)
async def select_candidate(callback: types.CallbackQuery, state: FSMContext):
    """Хэндлер для подтверждения голосования"""

    data = await state.get_data()
    db.vote(data["code"], data["candidate"])  # Обновляем записи в бд
    await callback.message.delete()
    await callback.message.answer(f"*Спасибо!*\nВаш голос очень важен для нас",
                                  parse_mode="Markdown")
    await state.clear()  # Очищаем стейты


async def start():
    """Асинхронная функция для запуска диспатчера"""
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(start())

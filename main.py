from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from collections import defaultdict
import sqlite3
import os

STEP = defaultdict(lambda: None)
STEP_DATA = defaultdict(lambda: {})

CONN = sqlite3.connect("tbot.db")  # или :memory: чтобы сохранить в RAM
CURSOR = CONN.cursor()

bot = Bot('YOU_TOKEN')
dp = Dispatcher(bot)

btn_add = InlineKeyboardButton('Добавить новое место', callback_data='add')
btn_list = InlineKeyboardButton('Мои локации', callback_data='list')
btn_reset = InlineKeyboardButton('Удалить локации', callback_data='reset')
inline_kb1 = InlineKeyboardMarkup().add(btn_add, btn_list, btn_reset)


@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    await bot.send_message(msg.from_user.id, text="Выберте команду", reply_markup=inline_kb1)
    set_step(msg, 'add')


@dp.message_handler(commands=['help'])
async def help_(msg: types.Message):
    await bot.send_message(msg.from_user.id, text="Выберте команду", reply_markup=inline_kb1)
    set_step(msg, 'add')


@dp.callback_query_handler(lambda c: c.data == 'add')
async def add_command(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, 'Отправьте имя локации')
    set_step(callback_query, 'Name')


@dp.message_handler(lambda msg: get_step(msg) == 'Name')
async def name_command(msg: types.Message):
    await bot.send_message(msg.from_user.id, 'Отправьте изображение локации')
    set_step(msg, 'Img')
    set_step_data(msg, {'name': msg.text})


@dp.message_handler(content_types=["photo"])
async def set_photo(msg):
    if get_step(msg) == 'Img':
        try:
            file_info = await bot.get_file(msg.photo[0].file_id)
            downloaded_file = await bot.download_file(file_info.file_path)
            src = f'{msg.photo[0].file_id}.jpg'
            with open(src, 'wb') as new_file:
                new_file.write(downloaded_file.getvalue())

            await bot.send_message(msg.from_user.id, "Пришлите, пожалуйста, локацию нового места")
            set_step(msg, 'Location')
            set_step_data(msg, {'photo': msg.photo[0].file_id})
        except:
            await bot.send_message(msg.from_user.id, 'На сервере произошла ошибка, попробуйте еще раз отправить '
                                                     'изображение либо смените формат фотографии')
    else:
        await bot.send_message(msg.from_user.id, 'Зачем мне это фото?')


@dp.message_handler(content_types=["location"])
async def location(msg):
    if msg.location is not None and get_step(msg) == 'Location':
        # Вставляем данные в таблицу
        sql = """INSERT INTO location
                          VALUES ('{user_id}', '{l_name}', '{l_img}', '{l_lat}', '{l_lon}')""".format(
            user_id=msg.from_user.id,
            l_name=STEP_DATA[msg.from_user.id]['name'],
            l_img=STEP_DATA[msg.from_user.id]['photo'],
            l_lat=msg.location.latitude,
            l_lon=msg.location.longitude
        )
        CURSOR.execute(sql)
        CONN.commit()
        await bot.send_message(msg.from_user.id, text='Локация добавлена', reply_markup=inline_kb1)
        set_step(msg, 'add')


@dp.callback_query_handler(lambda c: c.data == 'list')
@dp.message_handler(commands=['list'])
async def get_location_list(msg: types.Message):
    result = CURSOR.execute("SELECT * FROM location WHERE user_id='{user_id}' LIMIT 10".format(
        user_id=msg.from_user.id))
    if result.rowcount == -1:
        await bot.send_message(msg.from_user.id, text='Локации не найдены')

    for row in result:
        try:
            with open('{l_img}.jpg'.format(l_img=row[2]), 'rb') as photo:
                await bot.send_venue(msg.from_user.id, latitude=row[3], longitude=row[4], title=row[1], address='')
                await bot.send_photo(msg.from_user.id, photo=photo)
        except:
            pass
    await bot.send_message(msg.from_user.id, text='Выберте команду', reply_markup=inline_kb1)
    if 'id' in msg:
        await bot.answer_callback_query(msg.id)

    set_step(msg, 'add')


@dp.callback_query_handler(lambda c: c.data == 'reset')
@dp.message_handler(commands=['reset'])
async def reset(msg):
    result = CURSOR.execute("SELECT img FROM location WHERE user_id='{user_id}'".format(
        user_id=msg.from_user.id))
    for row in result:
        try:
            os.remove('{l_img}.jpg'.format(l_img=row[0]))
        except Exception as e:
            print('Файл не найден: {e}'.format(e=e))

    sql = """DELETE From location WHERE user_id='{user_id}'""".format(user_id=msg.from_user.id)
    CURSOR.execute(sql)
    CONN.commit()
    await bot.send_message(msg.from_user.id, text='Локации удалены', reply_markup=inline_kb1)
    if 'id' in msg:
        await bot.answer_callback_query(msg.id)

    set_step(msg, 'add')


@dp.message_handler()
async def all_handler(message: types.Message):
    await bot.send_message(message.from_user.id, 'Я понимаю только команды /start, /help, /add, /list и /reset')


def set_step(message, step):
    STEP[message.from_user.id] = step


def set_step_data(message, data):
    STEP_DATA[message.from_user.id].update(data)


def get_step(message):
    return STEP[message.chat.id]


if __name__ == '__main__':
    executor.start_polling(dp)

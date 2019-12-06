from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from collections import defaultdict
import sqlite3

STEP = defaultdict(lambda: 1)
conn = sqlite3.connect("tbot.db") # или :memory: чтобы сохранить в RAM
CURSOR = conn.cursor()

bot = Bot("992551165:AAEmEypkljG19yBr3iJSXVj4FlODSiFifRA")
dp = Dispatcher(bot)

btn_add = InlineKeyboardButton('Добавить новое место', callback_data='add')
btn_list = InlineKeyboardButton('Мои локации', callback_data='list')
btn_reset = InlineKeyboardButton('Удалить локации', callback_data='reset')
inline_kb1 = InlineKeyboardMarkup().add(btn_add, btn_list, btn_reset)


@dp.message_handler(commands=['start'])
async def process_command_1(message: types.Message):
    await message.reply("Выберте команду", reply_markup=inline_kb1)
    set_step(message, 'add')

@dp.callback_query_handler(lambda c: c.data == 'add')
async def start_add_location(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, 'Отправьте имя локации')
    set_step(callback_query, 'Name')


@dp.message_handler(lambda msg: get_step(msg) == 'Name')
async def step_name(msg: types.Message):
    await bot.send_message(msg.from_user.id, 'Отправьте изображение локации')
    set_step(msg, 'Img')


@dp.message_handler(lambda msg: get_step(msg) == 'Img')
async def step_img(msg: types.Message):
    await msg.reply('Локация добавлена', reply_markup=inline_kb1)
    set_step(msg, 'Img')


@dp.message_handler()
async def echo_message(msg: types.Message):
    await bot.send_message(msg.from_user.id, msg.text)


def set_step(message, step):
    STEP[message.from_user.id] = step


def get_step(message):
    return STEP[message.chat.id]


@dp.message_handler(commands=['list'])
async def cats(message: types.Message):
    with open('img/cats.jpg', 'rb') as photo:
        await message.reply_photo(photo, caption='Cats are here 😺')


@dp.message_handler(content_types=["photo"])
async def send_photo(message):
    if get_step(message) == 'Img':
        try:
          file_info = await bot.get_file(message.photo[0].file_id)
          downloaded_file = await bot.download_file(file_info.file_path)
          src = f'img/{message.photo[0].file_id}.jpg';
          with open(src, 'wb') as new_file:
              new_file.write(downloaded_file.getvalue())
          # Вставляем данные в таблицу
          cursor.execute("""INSERT INTO albums
                            VALUES ('Glow', 'Andy Hunter', '7/24/2012',
                            'Xplore Records', 'MP3')"""
                        )
          
          # Сохраняем изменения
          conn.commit()
          await bot.send_message(message.from_user.id, "Я сохранил новую локацию")
        except Exception as e:
          await bot.send_message(message.from_user.id, e)
    else:
        await bot.send_message(message.from_user.id, 'Зачем мне это фото?')


@dp.message_handler()
async def all_handler(message: types.Message):
    await bot.send_message(message.from_user.id, 'Я понимаю только команды /start, /add, /list и /reset')


if __name__ == '__main__':
    executor.start_polling(dp)

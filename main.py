from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from collections import defaultdict

STEP = defaultdict(lambda: 1)

bot = Bot("992551165:AAEmEypkljG19yBr3iJSXVj4FlODSiFifRA")
dp = Dispatcher(bot)

btn_add = InlineKeyboardButton('Добавить новое место', callback_data='add')
btn_list = InlineKeyboardButton('Мои локации', callback_data='list')
btn_reset = InlineKeyboardButton('Удалить локации', callback_data='reset')
inline_kb1 = InlineKeyboardMarkup().add(btn_add, btn_list, btn_reset)


@dp.message_handler(commands=['start'])
async def process_command_1(message: types.Message):
    await message.reply("Выберте команду", reply_markup=inline_kb1)


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
 
executor.start_polling(dp)

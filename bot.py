import asyncio
import logging
import sys
from os import environ

import pandas as pd
from dotenv import find_dotenv, load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.markdown import hbold
from aiogram.filters.command import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from aiogram import F, Router
from aiogram.fsm.state import State, StatesGroup, default_state
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

load_dotenv(find_dotenv('token.env'))
TOKEN = environ["BOT_TOKEN"]
data = pd.read_csv('data/database.csv')

# текст для команды help
HELP_COMMAND = '''
<b>/start</b> - <em>начинает работу бота</em>
<b>/help</b> - <em>показывает список команд</em>
<b>/description</b> - <em>показывает описание бота</em>
<b>/characteristics</b> - <em>выводит характеристики выбранного автомобиля</em>
'''
# текст для команды description
DESC_COMMAND = '''
Данный бот предназначен для того, чтобы:
<pre>- быстро и легко найти краткие и полные технические характеристики автомобиля;</pre>
<pre>- посмотреть фотографию автомобиля;</pre>
<pre>- найти все автомобили определнной марки на Авто.ру;</pre>
<pre>- узнать описание автомобиля.</pre>
'''

alphabet = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U',
            'V', 'W', 'X', 'Y', 'Z']
NAMES = list(data['name'].values)
MODELS = list(data['model'].values)

storage = MemoryStorage()
dp = Dispatcher(storage=storage)


class UserState(StatesGroup):
    CAR_NAME = State()


# обработчик команды start
@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f"Привет, {hbold(message.from_user.full_name)}! Чтобы узнать команды, введите /help")


# обработчик команды help
@dp.message(Command('help'))
async def help_command(message: types.Message):
    await message.reply(text=HELP_COMMAND, parse_mode='HTML')
    await message.delete()


# обработчик команды description
@dp.message(Command('description'))
async def desc_command(message: types.Message):
    await message.answer(text=DESC_COMMAND, parse_mode='HTML')
    await message.delete()

# обработчик команды characteristics

async def keyboard_main():
    buttons = []
    for key in range(0, len(alphabet) - 2, 3):
        buttons.append([KeyboardButton(text=f"{alphabet[key]}"),
                        KeyboardButton(text=f"{alphabet[key + 1]}"),
                        KeyboardButton(text=f"{alphabet[key + 2]}")])
    buttons.append([KeyboardButton(text=f"{alphabet[len(alphabet) - 2]}"),
                    KeyboardButton(text=f"{alphabet[len(alphabet) - 1]}")])

    keyboard = ReplyKeyboardMarkup(keyboard=buttons)
    return keyboard


@dp.message(Command('characteristics'))
async def characteristics_command(message: types.Message):

    await message.reply(text='Выберете на какую букву начинается марка автомобиля:', reply_markup=await keyboard_main())
    await message.delete()


@dp.message(F.text.in_({i for i in alphabet}))
async def callback_model(message: types.Message):
    models = data[data['model'].str[0] == message.text]['model'].sort_values().unique()
    buttons = [[KeyboardButton(text='Вернуться в основное меню')]]
    for key in models:
        buttons.append([KeyboardButton(text=f"{key}")])
    keyboard_names = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=buttons)

    await message.answer(text='Выберете модель автомобиля:', reply_markup=keyboard_names)


@dp.message(F.text.in_({i for i in MODELS}))
async def callback_name(message: types.Message, state=FSMContext):
    names_auto = data[data['model'] == message.text]['name'].sort_values().unique()
    buttons = [[KeyboardButton(text='Вернуться в основное меню')]]
    for key in names_auto:
        buttons.append([KeyboardButton(text=f"{key}")])
    keyboard_names = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=buttons)

    await message.answer(text='Выберете автомобиль:', reply_markup=keyboard_names)
    await state.set_state(UserState.CAR_NAME)


@dp.message(F.text.in_({i for i in NAMES}))
async def callback_functional(message: types.Message, state=FSMContext):
    buttons = [[KeyboardButton(text='Вернуться в основное меню')],
               [KeyboardButton(text='Краткая тех. характеристика'), KeyboardButton(text='Полная тех. характеристика')],
               [KeyboardButton(text='Фотография автомобиля'), KeyboardButton(text='Описание автомобиля')],
               [KeyboardButton(text='Поиск марки автомобиля на Авто.ру')]]

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=buttons, one_time_keyboard=True)
    await message.answer(text='Что вы хотите узнать об автомобиле?', reply_markup=keyboard)
    await state.update_data(CAR_NAME=message.text)


@dp.message(F.text == 'Краткая тех. характеристика')
async def characteristics(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    auto = user_data['CAR_NAME']
    # тип кузова
    carcass = data[data['name'] == auto]['carcass'].values[0]
    # год выпуска
    release_year = data[data['name'] == auto]['release_year'].values[0]
    # количество дверей
    doors = data[data['name'] == auto]['doors'].values[0]
    # объём двигателя
    volume = data[data['name'] == auto]['volume'].values[0]
    # количество лошадиных сил
    power = data[data['name'] == auto]['power'].values[0]

    text_for_user = f'''
    <b>Год выпуска:</b> {release_year} 
    <b>Тип кузова:</b> {carcass} 
    <b>Количество дверей:</b> {doors} 
    <b>Объём двигателя:</b> {volume} 
    <b>Количество лошадиных сил:</b> {power} 
    '''

    await message.answer(text=text_for_user, parse_mode='HTML')


@dp.message(F.text == 'Полная тех. характеристика')
async def over_characteristics(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    auto = user_data['CAR_NAME']
    # выбор фотографии с техническими характеристиками
    url_photo = data[data['name'] == auto]['full_characteristics_url'].values[0]

    await message.answer_photo(url_photo)


@dp.message(F.text == 'Фотография автомобиля')
async def image_auto(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    auto = user_data['CAR_NAME']
    # выбор фотографии с техническими характеристиками
    url_photo = data[data['name'] == auto]['image_auto_url'].values[0]
    if url_photo == 'None':
        await message.answer('Извините, на данный момент у нас нет фотографий этого автомобиля')
        await state.clear()
    else:
        await message.answer_photo(url_photo)


@dp.message(F.text == 'Описание автомобиля')
async def image_auto(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    auto = user_data['CAR_NAME']
    # выбор фотографии с техническими характеристиками
    description = data[data['name'] == auto]['desription_auto'].values[0]
    if len(description) < 5:
        await message.answer(text='Данный автомобиль не имеет никакой информации.')
    else:
        await message.answer(text=description)


@dp.message(F.text == 'Поиск марки автомобиля на Авто.ру')
async def search_auto(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    auto = user_data['CAR_NAME']
    # выбор фотографии с техническими характеристиками
    model = data[data['name'] == auto]['model'].values[0]
    url = f'https://auto.ru/moskva/cars/{model}/all/'
    await message.reply(f'<a href="{url}">Ссылка на авто.ру</a>', parse_mode="HTML")


@dp.message(F.text == 'Вернуться в основное меню')
async def return_main(message: types.Message, state: FSMContext):
    await message.answer(text='Выберете на какую букву начинается марка автомобиля:', reply_markup=await keyboard_main())
    await state.clear()


async def main() -> None:
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
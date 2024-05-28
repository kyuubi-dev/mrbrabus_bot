from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import types

def main():
    Main = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text ="📰 Отправить объявление", callback_data='submit')
    ]
    ])
    return Main

def submit():
    Submit = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text ="🔙 Назад", callback_data='main_menu')
    ]
    ])
    return Submit
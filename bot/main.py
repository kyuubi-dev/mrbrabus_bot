import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, callback_query, FSInputFile, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart, Command
# Other

from bot import keyboard as kb
from config import bot_token, admin

bot = Bot(token=bot_token)

class Form(StatesGroup):
    waiting_for_img = State()
    waiting_for_description = State()
    waiting_for_contact = State()

def startBOT(dp: Dispatcher):
    @dp.message(CommandStart())
    async def cmd_start(message: Message, state: FSMContext):
        user_id = message.from_user.id
        name = message.from_user.first_name
        if name is None:
            name = message.from_user.last_name
        
        await message.answer(text=f"👋 Привет *{name}*, здесь ты можешь отправить свое объявление на проверку\n\n*После проверки вам отправиться сообщение об результате*", reply_markup=kb.main(), parse_mode="Markdown")
        
    @dp.callback_query(F.data == 'submit')
    async def submit_processing(callback_query: types.CallbackQuery, state: FSMContext):
        await state.set_state(Form.waiting_for_img)
        await callback_query.message.edit_text(f"🖼 Отпрьте фото объявления", reply_markup=kb.submit(), parse_mode='Markdown')

    @dp.callback_query(F.data == 'main_menu')
    async def submit_processing(callback_query: types.CallbackQuery, state: FSMContext):
        await callback_query.message.delete()
        name = callback_query.from_user.first_name
        if name is None:
            name = callback_query.from_user.last_name
        
        await callback_query.message.answer(text=f"👋 Привет *{name}*, здесь ты можешь отправить свое объявление на проверку\n\n*После проверки вам отправиться сообщение об результате*", reply_markup=kb.main(), parse_mode="Markdown")

    @dp.message(Form.waiting_for_img)
    async def process_img(message: Message, state: FSMContext):
        if message.photo:
            await state.update_data(photo=message.photo[-1])
            await message.answer("👌 Фото получено, отправьте описание")
            await state.set_state(Form.waiting_for_description)
        else:
            await message.answer("❌ Неверный формат...")

    @dp.message(Form.waiting_for_description)
    async def process_description(message: Message, state: FSMContext):
        await state.update_data(description=message.text)
        await message.answer("✅ Описание получено, отправьте контактные данные")
        await state.set_state(Form.waiting_for_contact)

    @dp.message(Form.waiting_for_contact)
    async def process_contact(message: Message, state: FSMContext):
        await state.update_data(contact=message.text)
        await message.answer("✅ Контактные данные получены, начинаем проверку...")

        user_data = await state.get_data()
        photo = user_data['photo']
        description = user_data['description']
        contact = user_data['contact']

        user_photo_id = f"{message.from_user.id}_{photo.file_id[:10]}"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Принять", callback_data=f"accept_{user_photo_id}"),
                InlineKeyboardButton(text="Отклонить", callback_data=f"reject_{user_photo_id}")
            ]
        ])

        admin_message = (
            f"*Описание*:\n{description}\n\n"
            f"*Контакты*: {contact}"
        )
        await bot.send_photo(admin, photo.file_id, caption=admin_message, reply_markup=keyboard, parse_mode='Markdown')

        await state.clear()

    async def send_post_to_channel(photo_id: str, description: str, contact: str):
        channel_username = "@test_3213"
        admin_message = (
            f"Описание:\n{description}\n\n"
            f"Контакты: {contact}"
        )
        await bot.send_photo(channel_username, photo_id, caption=admin_message)

    @dp.callback_query(lambda c: c.data.startswith('accept_') or c.data.startswith('reject_'))
    async def process_decision(callback_query: CallbackQuery, state: FSMContext):
        action, user_photo_id = callback_query.data.split('_', 1)
        user_id, file_id_part = user_photo_id.split('_', 1)

        user_data = await state.get_data()
        if 'photo' in user_data:
            photo = user_data['photo']
            description = user_data['description']
            contact = user_data['contact']

            if action == 'accept':
                await bot.send_message(user_id, "✅ Ваше объявление принято!")
                await send_post_to_channel(photo.file_id, description, contact)
                await callback_query.answer("Объявление принято")
            elif action == 'reject':
                await bot.send_message(user_id, "❌ Ваше объявление отклонено.")
                await callback_query.answer("Объявление отклонено")
        else:
            await callback_query.answer("Ошибка: Фото не найдено в данных пользователя")


    @dp.callback_query(F.data == 'accepted')
    async def accepted_processing(callback_query: types.CallbackQuery, state: FSMContext):
        await callback_query.answer("Объявление уже принято")
    
    @dp.callback_query(F.data == 'rejected')
    async def rejected_processing(callback_query: types.CallbackQuery, state: FSMContext):
        await callback_query.answer("Объявление уже отклонено")
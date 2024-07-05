import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters.state import StateFilter

from bot import keyboard as kb
from config import bot_token, admin

bot = Bot(token=bot_token)

class Form(StatesGroup):
    waiting_for_announcement = State()
    waiting_for_img = State()
    waiting_for_contact = State()
    waiting_for_edit = State()

def startBOT(dp: Dispatcher):
    @dp.message(CommandStart())
    async def cmd_start(message: Message, state: FSMContext):
        await state.clear()
        name = message.from_user.first_name
        if name is None:
            name = message.from_user.last_name
        
        await message.answer(
            text=f"👋 Привет *{name}*, составьте сообщение с текстом Вашего объявления и нажмите отправить.",
            parse_mode="Markdown"
        )
        await state.set_state(Form.waiting_for_announcement)

    @dp.message(StateFilter(Form.waiting_for_announcement))
    async def process_announcement(message: Message, state: FSMContext):
        await state.update_data(description=message.text)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Нет", callback_data="no_image")]
        ])
        
        await message.answer(
            text="Приложите одну картинку если желаете показать её в объявлении",
            reply_markup=keyboard
        )
        await state.set_state(Form.waiting_for_img)

    @dp.callback_query(lambda c: c.data == 'no_image', StateFilter(Form.waiting_for_img))
    async def no_image(callback_query: CallbackQuery, state: FSMContext):
        await callback_query.message.answer("Укажите в сообщении как с вами могут связаться")
        await state.set_state(Form.waiting_for_contact)

    @dp.message(StateFilter(Form.waiting_for_img))
    async def process_img(message: Message, state: FSMContext):
        if message.photo:
            await state.update_data(photo=message.photo[-1].file_id)
            await message.answer("✅ Фото получено. Укажите в сообщении как с вами могут связаться")
            await state.set_state(Form.waiting_for_contact)
        else:
            await message.answer("❌ Неверный формат. Пожалуйста, отправьте фото или нажмите 'Нет'.")

    @dp.message(StateFilter(Form.waiting_for_contact))
    async def process_contact(message: Message, state: FSMContext):
        await state.update_data(contact=message.text)
        await message.answer("Объявление проверяется модератором.")

        user_data = await state.get_data()
        description = user_data['description']
        contact = user_data['contact']
        photo = user_data.get('photo')

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Принять", callback_data=f"accept_{message.from_user.id}")],
            [InlineKeyboardButton(text="Отклонить", callback_data=f"reject_{message.from_user.id}")],
            [InlineKeyboardButton(text="Редактировать", callback_data=f"edit_{message.from_user.id}")]
        ])


        admin_message = (
            f"❗️ {description}\n\n"
            f"🔍 *{contact}*"
        )

        if photo:
            await bot.send_photo(admin, photo, caption=admin_message, reply_markup=keyboard, parse_mode='Markdown')
        else:
            await bot.send_message(admin, admin_message, reply_markup=keyboard, parse_mode='Markdown')

        await state.clear()

    @dp.callback_query(lambda c: c.data.startswith('accept_') or c.data.startswith('reject_'))
    async def process_decision(callback_query: CallbackQuery, state: FSMContext):
        action, user_id = callback_query.data.split('_')
        user_id = int(user_id)

        original_message = callback_query.message

        if action == 'accept':
            await bot.send_message(user_id, "✅ Ваше объявление принято!")

            await original_message.edit_reply_markup()

            channel_username = "@gollandka"
            # channel_username = "@test_31031"

            original_caption = original_message.caption
            original_photo = None

            if original_message.photo:
                original_photo = original_message.photo[-1].file_id
                await bot.send_photo(channel_username, original_photo, caption=original_caption, parse_mode='Markdown')
            else:
                original_text = original_message.text
                await bot.send_message(channel_username, original_text)

            await callback_query.answer("Объявление принято")

        elif action == 'reject':
            await bot.send_message(user_id, "❌ Ваше объявление отклонено.")
            await original_message.edit_reply_markup(
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="❌ Отклонено", callback_data="rejected")]
                ])
            )
            await callback_query.answer("Объявление отклонено")

    @dp.callback_query(lambda c: c.data.startswith('edit_'))
    async def process_edit(callback_query: CallbackQuery, state: FSMContext):
        action, user_id = callback_query.data.split('_')
        user_id = int(user_id)
        
        original_caption = callback_query.message.caption if callback_query.message.caption else callback_query.message.text
        original_photo_id = callback_query.message.photo[-1].file_id if callback_query.message.photo else None

        await state.update_data(
            original_caption=original_caption,
            original_photo_id=original_photo_id,
            user_id=user_id,
            message_id=callback_query.message.message_id,
            message_reply_markup=callback_query.message.reply_markup
        )
        
        await bot.send_message(admin, "✏️ Пожалуйста, отправьте новый текст для объявления.")

        await state.set_state(Form.waiting_for_edit)

    @dp.message(StateFilter(Form.waiting_for_edit))
    async def process_new_text(message: Message, state: FSMContext):
        user_data = await state.get_data()
        new_text = message.text
        original_photo_id = user_data.get('original_photo_id')
        original_message_id = user_data.get('message_id')
        message_reply_markup = user_data.get('message_reply_markup')

        if original_photo_id:
            await bot.edit_message_caption(
                chat_id=admin,
                message_id=original_message_id,
                caption=new_text,
                reply_markup=message_reply_markup,
                parse_mode='Markdown'
            )
        else:
            await bot.edit_message_text(
                chat_id=admin,
                message_id=original_message_id,
                text=new_text,
                reply_markup=message_reply_markup,
                parse_mode='Markdown'
            )
        await bot.send_message(admin, "✅ Готово.")

        await state.clear()

    @dp.callback_query(lambda c: c.data == 'rejected')
    async def rejected_processing(callback_query: CallbackQuery, state: FSMContext):
        await callback_query.answer("Объявление уже отклонено")

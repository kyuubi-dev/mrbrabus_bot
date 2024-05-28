import asyncio
from aiogram import Bot, Dispatcher
from bot.main import startBOT

import config as cfg

bot = Bot(token=cfg.bot_token)
dp = Dispatcher()

startBOT(dp)

async def start_bot():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(start_bot())
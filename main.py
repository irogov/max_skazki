import aiomax, asyncio, os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from services.fairytale import send_daily_story
from openai import AsyncOpenAI
from aiomax.types import FileAttachment

env = environs.Env()
env.read_env()
MAX_TOKEN = os.environ.get('MAX_TOKEN')
DEEPSEEK_TOKEN = os.environ.get('DEEPSEEK_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
client = AsyncOpenAI(api_key=DEEPSEEK_TOKEN, base_url="https://api.deepseek.com")

bot = aiomax.Bot(MAX_TOKEN)


async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        send_daily_story,
        'interval',
        minutes=1,
        # 'cron',
        # hour=19,
        args=[bot, CHAT_ID, client],  # Передаем экземпляр бота в функцию
        timezone="Europe/Moscow",
    )
    scheduler.start()
    await bot.start_polling()

if __name__ == '__main__':
    asyncio.run(main())
# bot.run()
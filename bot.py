import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from config.config import BOT_TOKEN, ADMIN_ID
from handlers.main import register_handlers
from database.db import init_db
import logging
from handlers.reports import start_report_scheduler

# Настройка логгирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN)

def is_admin(user_id):
    return user_id == ADMIN_ID

# Инициализация базы данных
init_db()

# Регистрация всех обработчиков
register_handlers(bot)

# Запуск планировщика отчетов
start_report_scheduler(bot)

if __name__ == '__main__':
    logger.info("Бот запущен")
    bot.infinity_polling()
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
from collections import defaultdict
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)

# Load bot token and admin ID from environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

# Directory for spam phrases
SPAM_PHRASES_DIR = os.path.join(os.path.dirname(__file__), "spam_phrases")

# Function to load spam phrases from a file
def load_spam_phrases(language: str) -> list:
    file_path = os.path.join(SPAM_PHRASES_DIR, f"{language}.txt")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            phrases = [line.strip().lower() for line in f if line.strip()]
        return phrases
    except FileNotFoundError:
        logging.error(f"Spam phrases file for '{language}' not found.")
        return []

# Load phrases for English and Russian
ENGLISH_SPAM_PHRASES = load_spam_phrases("english")
RUSSIAN_SPAM_PHRASES = load_spam_phrases("russian")

# Track spam statistics by group chat
group_spam_count = defaultdict(int)

# Middleware to handle spam detection and message deletion
class SpamMiddleware(BaseMiddleware):
    async def on_process_message(self, message: types.Message, data: dict):
        language = detect_language(message.text)
        if is_spam(message.text, language):
            group_id = message.chat.id
            group_spam_count[group_id] += 1
            await message.delete()
            raise CancelHandler()  # Cancel further message handling

# Function to detect message language (basic)
def detect_language(text: str) -> str:
    russian_chars = set("абвгдеёжзийклмнопрстуфхцчшщьыъэюя")
    english_chars = set("abcdefghijklmnopqrstuvwxyz")
    
    text_chars = set(text.lower())
    
    if len(text_chars & russian_chars) > len(text_chars & english_chars):
        return "ru"
    else:
        return "en"

# Function to check if message contains spam phrases
def is_spam(text: str, language: str) -> bool:
    if language == "ru":
        return any(phrase in text.lower() for phrase in RUSSIAN_SPAM_PHRASES)
    elif language == "en":
        return any(phrase in text.lower() for phrase in ENGLISH_SPAM_PHRASES)
    else:
        return False

# Command: /fstat - Show the number of flagged spam messages for the current chat
@dp.message_handler(commands=['fstat'])
async def show_spam_stat(message: types.Message):
    group_id = message.chat.id
    spam_count = group_spam_count.get(group_id, 0)
    await message.answer(f"Total flagged spam messages in this chat: {spam_count}")

# Admin-only command: /add_phrase - Add a new spam phrase to the filter (Only for memory, not saving to file)
@dp.message_handler(commands=['add_phrase'], user_id=ADMIN_ID)  # Using ADMIN_ID from .env
async def add_spam_phrase(message: types.Message):
    args = message.get_args()
    if not args:
        await message.reply("Please provide a phrase to add.")
        return

    ENGLISH_SPAM_PHRASES.append(args.lower())
    RUSSIAN_SPAM_PHRASES.append(args.lower())
    await message.reply(f"Phrase '{args}' has been added to the spam filter.")

# Start command handler
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Welcome! This bot filters spam messages and tracks spam stats for this chat.")

# Help command handler
@dp.message_handler(commands=['help'])
async def send_help(message: types.Message):
    help_text = ("This bot automatically filters spam messages based on phrases "
                 "and tracks flagged spam messages in the chat. Use /fstat to view "
                 "the spam statistics for this group.")
    await message.reply(help_text)

# Add SpamMiddleware to the dispatcher
dp.middleware.setup(SpamMiddleware())

# Run the bot
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

import logging
import os
import threading
from typing import List, Dict

from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.middlewares import BaseMiddleware
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
SPAM_PHRASES_FILE = "spam_phrases.txt"
FLAGGED_MESSAGES_FILE = "flagged_messages.txt"

# --- Global Variables ---
spam_phrases: Dict[str, List[str]] = {}  # Using a dictionary for language-specific phrases
flagged_message_counts: Dict[str, int] = {}
file_lock = threading.Lock()

# --- Bot Initialization ---
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Helper Functions ---

def load_spam_phrases():
    """Loads spam phrases from the specified file."""
    global spam_phrases
    with open(SPAM_PHRASES_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if ":" not in line:
                continue
            language, phrase = line.strip().split(":", 1)
            language = language.strip().lower()
            phrase = phrase.strip().lower()
            if language not in spam_phrases:
                spam_phrases[language] = []
            spam_phrases[language].append(phrase)

def load_flagged_message_counts():
    """Loads flagged message counts from the file."""
    global flagged_message_counts
    try:
        with open(FLAGGED_MESSAGES_FILE, "r") as f:
            for line in f:
                if ":" not in line:
                    continue
                group_id, count = line.strip().split(":")
                flagged_message_counts[group_id] = int(count)
    except FileNotFoundError:
        logging.warning("Flagged messages file not found. Starting fresh.")

def save_flagged_message_counts():
    """Saves flagged message counts to the file."""
    with open(FLAGGED_MESSAGES_FILE, "w") as f:
        for group_id, count in flagged_message_counts.items():
            f.write(f"{group_id}:{count}\n")

def detect_language(text: str) -> str:
    """Basic language detection (English or Russian)."""
    russian_chars = set("абвгдеёжзийклмнопрстуфхцчшщьыъэюя")
    english_chars = set("abcdefghijklmnopqrstuvwxyz")

    text_chars = set(text.lower())
    if len(text_chars & russian_chars) > len(text_chars & english_chars):
        return "ru"
    return "en"

def is_spam(text: str, language: str) -> bool:
    """Checks if the message contains spam phrases (substring match)."""
    text_lower = text.lower()
    for phrase in spam_phrases.get(language, []):
        if phrase in text_lower:
            return True
    return False

# --- Middleware ---
class SpamMiddleware(BaseMiddleware):
    async def on_process_message(self, message: types.Message, data: dict):
        language = detect_language(message.text)
        if is_spam(message.text, language):
            logging.info("SpamMiddleware triggered!")
            logging.info(f"Spam detected: {message.text}")
            group_id = str(message.chat.id)
            with file_lock:
                flagged_message_counts[group_id] = flagged_message_counts.get(group_id, 0) + 1
                save_flagged_message_counts()
            try:
                await message.delete()
            except Exception as e:
                logging.error(f"Failed to delete message: {e}")


# --- Handlers ---
@dp.message_handler(commands=['fstat'])
async def show_spam_stat(message: types.Message):
    group_id = str(message.chat.id)
    spam_count = flagged_message_counts.get(group_id, 0)
    await message.delete()
    await message.answer(f"This group has {spam_count} flagged spam messages.")

@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.reply("This bot filters spam messages.") 

@dp.message_handler(content_types=types.ContentType.TEXT)
async def handle_text_messages(message: types.Message):
    # This handler captures all text messages.
    # The spam middleware will automatically check for spam.
    pass

# --- Startup and Polling ---
if __name__ == '__main__':
    load_spam_phrases()
    load_flagged_message_counts()
    dp.middleware.setup(SpamMiddleware())
    executor.start_polling(dp, skip_updates=True)
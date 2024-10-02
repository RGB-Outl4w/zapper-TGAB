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

# File to store flagged message counts for each group
FLAGGED_MESSAGES_FILE = os.path.join(os.path.dirname(__file__), "flagged_messages.txt")

# Ensure flagged messages file exists
if not os.path.exists(FLAGGED_MESSAGES_FILE):
    with open(FLAGGED_MESSAGES_FILE, 'w') as f:
        pass

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
GERMAN_SPAM_PHRASES = load_spam_phrases("german")
FRENCH_SPAM_PHRASES = load_spam_phrases("french")
ITALIAN_SPAM_PHRASES = load_spam_phrases("italian")
VIETNAMESE_SPAM_PHRASES = load_spam_phrases("vietnamese")
CHINESE_SPAM_PHRASES = load_spam_phrases("chinese")
UKRAINIAN_SPAM_PHRASES = load_spam_phrases("ukrainian")
HINDI_SPAM_PHRASES = load_spam_phrases("hindi")
JAPANESE_SPAM_PHRASES = load_spam_phrases("japanese")

# Track spam statistics by group chat
group_spam_count = defaultdict(int)

# Middleware to handle spam detection and message deletion
class SpamMiddleware(BaseMiddleware):
    async def on_process_message(self, message: types.Message, data: dict):
        language = detect_language(message.text)
        if is_spam(message.text, language):
            group_id = str(message.chat.id)
            increment_flagged_message_count(group_id)
            await message.delete()
            raise CancelHandler()  # Cancel further message handling

# Function to detect message language (basic)
def detect_language(text: str) -> str:
    russian_chars = set("абвгдеёжзийклмнопрстуфхцчшщьыъэюя")
    english_chars = set("abcdefghijklmnopqrstuvwxyz")
    spanish_chars = set("abcdefghijklmnñopqrstuvwxyz")
    german_chars = set("abcdefghijklmnopqrstuvwxyzß")
    french_chars = set("abcdefghijklmnopqrstuvwxyz")
    chinese_chars = set("āáǎàēéěèīíǐìōóǒòūúǔùüǘǚǜㄅㄆㄇㄈㄉㄊㄋㄌㄍㄎㄏㄐㄑㄒㄓㄔㄕㄖㄗㄘㄙㄚㄛㄜㄝㄞㄟㄠㄡㄢㄣㄤㄥㄦㄧㄨㄩ")
    japanese_chars = set("あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん")
    vietnamese_chars = set("aăâbcdđeêghiklmnonpqrstuưvxy")
    italian_chars = set("abcdefghijklmnopqrstuvwxyz")
    ukrainian_chars = set("абвгґдеєжзиїйклмнопрстуфхцчшщьюя")
    hindi_chars = set("अआइईउऊऋऌएऐओऔकखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह")

    # Mapping languages to their character sets
    language_sets = {
        "ru": russian_chars,
        "en": english_chars,
        "es": spanish_chars,
        "de": german_chars,
        "fr": french_chars,
        "zh": chinese_chars,
        "ja": japanese_chars,
        "vi": vietnamese_chars,
        "it": italian_chars,
        "uk": ukrainian_chars,
        "hi": hindi_chars,
    }
    
    text_chars = set(text.lower())
    
    # Determine which language has the most character matches
    detected_language = max(language_sets, key=lambda lang: len(text_chars & language_sets[lang]))

    return detected_language

# Function to check if message contains spam phrases for multiple languages
def is_spam(text: str, language: str) -> bool:
    # Map each language to its respective spam phrases
    spam_phrases = {
        "ru": RUSSIAN_SPAM_PHRASES,
        "en": ENGLISH_SPAM_PHRASES,
        "es": SPANISH_SPAM_PHRASES,
        "de": GERMAN_SPAM_PHRASES,
        "fr": FRENCH_SPAM_PHRASES,
        "zh": CHINESE_SPAM_PHRASES,
        "ja": JAPANESE_SPAM_PHRASES,
        "vi": VIETNAMESE_SPAM_PHRASES,
        "it": ITALIAN_SPAM_PHRASES,
        "uk": UKRAINIAN_SPAM_PHRASES,
        "hi": HINDI_SPAM_PHRASES
    }

    # Get the spam phrases for the detected language (if available)
    phrases = spam_phrases.get(language)

    if phrases:
        return any(phrase in text.lower() for phrase in phrases)
    else:
        # Return False if no phrases for the detected language
        return False

# Function to read the flagged messages count for a specific group
def get_flagged_message_count(group_id: str) -> int:
    with open(FLAGGED_MESSAGES_FILE, "r") as f:
        for line in f:
            saved_group_id, count = line.strip().split(":")
            if saved_group_id == group_id:
                return int(count)
    return 0

# Function to increment the flagged message count for a group
def increment_flagged_message_count(group_id: str):
    counts = {}
    
    # Read current counts
    with open(FLAGGED_MESSAGES_FILE, "r") as f:
        for line in f:
            saved_group_id, count = line.strip().split(":")
            counts[saved_group_id] = int(count)
    
    # Increment count for the specific group
    if group_id in counts:
        counts[group_id] += 1
    else:
        counts[group_id] = 1
    
    # Write updated counts back to file
    with open(FLAGGED_MESSAGES_FILE, "w") as f:
        for gid, count in counts.items():
            f.write(f"{gid}:{count}\n")

# Command: /fstat - Show the number of flagged spam messages for the current chat
@dp.message_handler(commands=['fstat'])
async def show_spam_stat(message: types.Message):
    group_id = str(message.chat.id)
    spam_count = get_flagged_message_count(group_id)
    
    # Respond based on the number of flagged messages
    if spam_count == 0:
        await message.answer("This group is spotless! Not a single spam message flagged.")
    elif spam_count <= 5:
        await message.answer(f"Only {spam_count} spam messages flagged... This group is rather clean.")
    elif spam_count <= 100:
        await message.answer(f"{spam_count} spam messages flagged... Looks like the bot is doing its job!")
    elif spam_count <= 500:
        await message.answer(f"{spam_count} spam messages flagged... This group has seen some activity!")
    else:
        await message.answer(f"Wow! {spam_count} spam messages flagged... Lots of hard work was done here!")

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

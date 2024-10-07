# ⚡ Zapper: Telegram Anti-Spam Bot

A Telegram bot built using `aiogram` that automatically filters spam messages based on language-specific phrases and tracks spam statistics per group chat.

## Features

- Phrase-based spam detection for English and Russian
- Dynamic spam tracking per group chat that has this bot
- Supports additional languages by adding new phrases to `spam_phrases.txt` file
- Securely stores sensitive information like bot tokens in a `.env` file

## Project Structure
```
telegram-antispam-bot/
├── .env.example           # Example .env file
├── .gitignore             # To exclude sensitive files and Python caches
├── bot.py                 # Main bot script
├── requirements.txt       # Python dependencies
├── spam_phrases.txt       # Directory for spam phrase lists
├── README.md              # Documentation
└── README-ru.md           # Documentation on Russian
```

## Setup Instructions

1. **Clone the repository**:
   ```bash
   git clone https://github.com/RGB-Outl4w/zapper-TelegramAntispamBot.git
   cd zapper-TelegramAntispamBot
   ```

2. **Create and configure the .env file**:

  - **[OPTIONAL]** Copy the .env.example file to .env:
  ```bash
  cp .env.example .env
  ```

  - Edit the .env file to include your bot token and admin ID:
  ```bash
  BOT_TOKEN=your-bot-token-here
  ```

3. **Install the dependencies: Make sure you have Python installed. Then, install the required libraries**:
   ```bash
   pip install -r requirements.txt
   ```
   
4. **Add spam phrases**: Add spam phrases to the `spam_phrases.txt` and other files as needed. Each phrase should be on a new line and formatted in the following way:
   ```
   language:phrase
   ```

5. Run the bot:
   ```bash
   python bot.py
   ```

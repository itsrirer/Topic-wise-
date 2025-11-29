# Telegram Auto Topic Forward Bot

Caption-driven Pyrogram bot that creates forum topics in a destination group and forwards videos/documents into topic threads.

## 1-Click Deploy to Heroku
After you upload this repository to GitHub, use this button (replace the URL with your repo link):

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/YOUR_USERNAME/YOUR_REPO)

## Required Config Vars (Heroku > Settings > Config Vars)
- API_ID
- API_HASH
- BOT_TOKEN
- OWNER_ID

## Usage (after deploy & config)
1. Start the bot — it runs automatically on Heroku worker.
2. From OWNER account (OWNER_ID), run:
   - `/addsource -1001234567890` — add source channel/group id
   - `/adddest -1009876543210` — set destination forum group id
   - `/startforward` — enable forwarding
   - `/scanold` — process older messages
   - `/status` — check configuration
3. Caption format expected (example):

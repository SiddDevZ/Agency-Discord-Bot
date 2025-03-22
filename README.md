# LuvoBot

A Discord bot for the LuvoWeb Freelance server with ticket management, support features, and more.

## Features

- Ticket management system for orders and support
- Automatic message moderation using AI
- Command system for creating embeds and server information
- AI-powered /ask command for answering questions

## Setup

1. Clone this repository
2. Install Python 3.8+ 
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Configure your environment variables in the `.env` file:
   - `TOKEN`: Your Discord bot token
   - `GUILD`: Your Discord server/guild ID
   - `LOG_CHANNEL`: Channel ID for ticket transcripts
   - `ICON_URL`: URL for server icon to use in embeds
   - `CSS`: (Optional) Custom CSS for ticket transcripts
   
5. Run the bot:
   ```
   python bot.py
   ```

## Commands

- `-send`: Sets up the ticket panel (admin only)
- `-embed`: Creates the server welcome embed
- `-rules`: Posts server rules
- `-terms`: Posts terms of service
- `/ask`: Ask a question to the AI
- `/meme`: Get a random meme
- `/quote`: Get an inspirational quote
- `/version`: Show bot version information

## Environment Variables

The bot uses a `.env` file to store configuration. Make sure you have a properly configured `.env` file before running the bot.

## Note

This bot uses AI-powered content moderation and requires internet access for features like the `/ask` command. 
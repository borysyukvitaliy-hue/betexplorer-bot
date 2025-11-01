# BetExplorer Telegram Bot

## Overview
This is a Telegram bot that monitors BetExplorer for tennis betting odds movements. The bot scrapes the BetExplorer website every 10 minutes and sends notifications to a specified Telegram chat when it finds matches with significant odds drops.

## Project Type
Backend service - Telegram bot (no frontend)

## Architecture
- **Language**: Python 3.11
- **Main Libraries**:
  - `aiogram` - Telegram Bot framework
  - `requests` - HTTP requests for web scraping
  - `beautifulsoup4` - HTML parsing for scraping
  
## Features
- Monitors tennis odds movements on BetExplorer
- Sends Telegram notifications for matches with odds drops above threshold
- Configurable filters via Telegram commands
- Automatic data cleanup every 7 days
- Tracks known matches to avoid duplicate notifications

## Bot Commands
- `/start` or `/status` - Show current filter settings
- `/filtertime <time>` - Set time filter (1h, 3h, 6h, 12hours, 24hours, 48hours, 7days)
- `/filterdrop <percent>` - Set minimum drop percentage threshold

## Configuration
The bot uses two environment variables:
- `TELEGRAM_TOKEN` - Bot token from BotFather
- `TELEGRAM_CHAT_ID` - Chat ID where notifications will be sent

Filter settings are stored in `config.json`:
- `drops_in_last` - Time window for odds drops (default: 12hours)
- `matches_for` - Match timing filter (default: today)
- `min_drop_percent` - Minimum drop percentage (default: 25)

## Data Files
- `known_matches.json` - Tracks previously notified matches
- `last_clear.txt` - Timestamp of last data cleanup
- `config.json` - Bot configuration

## Recent Changes
- 2025-11-01: Upgraded to aiogram 3.4.1
  - Updated from aiogram 2.25.1 to 3.4.1 for modern Telegram bot features
  - Installed Flask for web status endpoint
  - Installed Playwright for advanced web scraping (optional)
  - Installed python-dotenv for environment variable management
  - Fixed SSL certificate verification for web scraping
  - Bot now monitors BetExplorer for tennis odds movements
  
- 2025-10-31: Initial setup for Replit environment
  - Installed Python 3.11 and dependencies
  - Fixed type safety issue with environment variables
  - Converted line endings from Windows to Unix format
  - Added .gitignore for Python project

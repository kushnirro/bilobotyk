# Bilobozhnytskyi Telegram Bot

Telegram bot for Bilobozhnytska community that provides information about:
- Weather
- Weather forecast
- News
- Holidays and significant dates
- Weather notifications

## Installation

1. Clone the repository
2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # for Linux/Mac
# or
venv\Scripts\activate  # for Windows
```
3. Install dependencies:
```bash
pip install -r requirements.txt
```
4. Create `.env` file based on `.env.example` and add necessary tokens
5. Run the bot:
```bash
python main.py
```

## Project Structure

```
bilobotyk/
├── src/           # Source code
├── logs/          # Logs
├── config.py      # Configuration
├── database.py    # Database operations
├── holidays.py    # Holidays processing
├── news.py        # News processing
├── main.py        # Main file
└── requirements.txt
```

## Configuration

Create `.env` file with the following variables:
```
BOT_TOKEN=your_bot_token
WEATHER_API_KEY=your_weather_api_key
``` 
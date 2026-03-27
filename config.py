import os
from dotenv import load_dotenv

load_dotenv()

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
DOUBAN_USER_ID = os.getenv("DOUBAN_USER_ID")
DOUBAN_COOKIES = os.getenv("DOUBAN_COOKIES")

RATE_LIMIT_DELAY = float(os.getenv("RATE_LIMIT_DELAY", "1.0"))
ENABLE_LOGGING = os.getenv("ENABLE_LOGGING", "true").lower() == "true"

import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    logger.error("No TELEGRAM_BOT_TOKEN found in environment variables!")

# The Telegram ID of your personal account where messages will be forwarded
OWNER_CHAT_ID = os.environ.get("OWNER_CHAT_ID")
if not OWNER_CHAT_ID:
    logger.error("No OWNER_CHAT_ID found in environment variables!")

# The secret token to secure the webhook
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")
if not WEBHOOK_SECRET:
    logger.warning("No WEBHOOK_SECRET found, webhook will not be secured!")

# Base URL where the webhook will be available
BASE_URL = os.environ.get("BASE_URL", "")
if not BASE_URL:
    logger.warning("No BASE_URL found, webhook cannot be registered automatically!")

# Flask configuration
PORT = int(os.environ.get("PORT", 5000))
HOST = "0.0.0.0"
DEBUG = os.environ.get("DEBUG", "True").lower() in ("true", "1", "t")
SESSION_SECRET = os.environ.get("SESSION_SECRET", "telegram-forwarding-bot-secret")

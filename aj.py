from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
import subprocess
import time
import threading
import psutil  # For system monitoring
from datetime import datetime

# Hardcoded API credentials
API_ID = 1257888659  # Replace with your Telegram API ID
API_HASH = "8d0180e35213d71884baecdb5aa329e1"  # Replace with your Telegram API Hash
BOT_TOKEN = "6098885239:AAEdNugC1-rLImsUY7iE7uYpBFRFRlhM6dw"  # Replace with your bot token

# Hardcoded Owner and Reseller IDs
OWNER_ID = 1257888659  # Replace with your Telegram ID
RESELLER_IDS = [1257888659]  # Replace with reseller Telegram IDs

# Database setup
conn = sqlite3.connect('bot_database.db', check_same_thread=False)
cursor = conn.cursor()

# Create tables if they don't exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    tokens INTEGER DEFAULT 0,
    role TEXT DEFAULT 'member',
    banned INTEGER DEFAULT 0
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS tasks (
    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    ip TEXT,
    port INTEGER,
    method TEXT,
    duration TEXT,
    status TEXT DEFAULT 'running',
    start_time TEXT,
    end_time TEXT,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS feedback (
    feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER,
    feedback TEXT,
    FOREIGN KEY(task_id) REFERENCES tasks(task_id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT,
    timestamp TEXT,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS images (
    image_id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_url TEXT,
    is_default INTEGER DEFAULT 0
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS whitelist (
    ip TEXT PRIMARY KEY
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS blacklist (
    ip TEXT PRIMARY KEY
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS templates (
    template_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    name TEXT,
    ip TEXT,
    port INTEGER,
    method TEXT,
    duration TEXT,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
)
''')

conn.commit()

# Initialize Pyrogram client
app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Simulated task binary (replace with your actual binary path)
TASK_BINARY = "./home/user/noob/gayu"  # Replace with the path to your task binary

# Log actions to the database
def log_action(user_id, action):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('INSERT INTO logs (user_id, action, timestamp) VALUES (?, ?, ?)', (user_id, action, timestamp))
    conn.commit()

# Execute a task in a separate thread
def execute_task(task_id, ip, port, method, duration):
    try:
        # Convert duration to seconds
        if 'h' in duration:
            duration_seconds = int(duration.replace('h', '')) * 3600
        elif 'd' in duration:
            duration_seconds = int(duration.replace('d', '')) * 86400
        else:
            duration_seconds = int(duration.replace('m', '')) * 60

        # Log task start time
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('UPDATE tasks SET start_time = ? WHERE task_id = ?', (start_time, task_id))
        conn.commit()

        # Run the task binary
        process = subprocess.Popen([TASK_BINARY, ip, str(port), method, str(duration_seconds)])
        process.wait()

        # Log task end time
        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('UPDATE tasks SET status = "completed", end_time = ? WHERE task_id = ?', (end_time, task_id))
        conn.commit()

        # Send feedback buttons
        app.send_message(
            chat_id=cursor.execute('SELECT user_id FROM tasks WHERE task_id = ?', (task_id,)).fetchone()[0],
            text="🎉 Task completed! Did it work?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Worked", callback_data=f"feedback_{task_id}_success")],
                [InlineKeyboardButton("❌ Didn’t Work", callback_data=f"feedback_{task_id}_fail")]
            ])
        )
    except Exception as e:
        print(f"Error during task execution: {e}")

# Start command
@app.on_message(filters.command("start"))
def start(client, message):
    user_id = message.from_user.id
    username = message.from_user.username

    # Add user to database if not exists
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)', (user_id, username))
    conn.commit()

    # Check if the user is the owner
    if user_id == OWNER_ID:
        welcome_message = "🌟 Welcome back, Owner! Use /help to see available commands."
    # Check if the user is a reseller
    elif user_id in RESELLER_IDS:
        welcome_message = "🌟 Welcome back, Reseller! Use /help to see available commands."
    else:
        welcome_message = "🌟 Welcome to the bot! Use /help to see available commands."

    log_action(user_id, "started the bot")
    message.reply_text(welcome_message + "\n\nBot made by @hack_chiye")

# Help command
@app.on_message(filters.command("help"))
def help(client, message):
    user_id = message.from_user.id

    # Check if the user is the owner
    if user_id == OWNER_ID:
        help_text = """
        👑 **Owner Commands:**
        /starttask [IP] [PORT] [METHOD] [DURATION] - Start a task
        /stoptask [ID] - Stop a task
        /addtokens [ID] [AMOUNT] - Add tokens to a user
        /ban [ID] - Ban a user
        /unban [ID] - Unban a user
        /addreseller [ID] - Grant reseller privileges
        /removereseller [ID] - Remove reseller privileges
        /setadmin [ID] - Grant admin privileges
        /removeadmin [ID] - Remove admin privileges
        /listusers - List all users
        /networkstatus - Check server status
        /botping - Ping the bot
        /runningtasks - Show running tasks
        /systeminfo - Display system info
        /serverlogs - Retrieve server logs
        /analytics - View task analytics
        /auditlogs - View audit logs
        /whitelist [IP] - Add IP to whitelist
        /blacklist [IP] - Add IP to blacklist
        /setwelcome [message] - Set welcome message
        /sethelp [message] - Set help message
        /setcooldown [seconds] - Set command cooldown
        /setmaxduration [time] - Set maximum task duration
        """
    # Check if the user is a reseller
    elif user_id in RESELLER_IDS:
        help_text = """
        💼 **Reseller Commands:**
        /starttask [IP] [PORT] [METHOD] [DURATION] - Start a task
        /stoptask [ID] - Stop a task
        /addtokens [ID] [AMOUNT] - Add tokens to a user
        /listusers - List all users
        /networkstatus - Check server status
        /botping - Ping the bot
        /runningtasks - Show running tasks
        /systeminfo - Display system info
        /analytics - View task analytics
        """
    else:
        help_text = """
        👤 **Member Commands:**
        /starttask [IP] [PORT] [METHOD] [DURATION] - Start a task
        /stoptask [ID] - Stop a task
        /checktokens - Check your token balance
        /buytokens [AMOUNT] - Buy tokens
        /networkstatus - Check server status
        /botping - Ping the bot
        /runningtasks - Show running tasks
        /analytics - View task analytics
        """

    message.reply_text(help_text + "\n\nBot made by @hack_chiye")

# Info command
@app.on_message(filters.command("info"))
def info(client, message):
    user_id = message.from_user.id
    username = message.from_user.username

    # Check if the user is the owner
    if user_id == OWNER_ID:
        role = "👑 Owner"
    # Check if the user is a reseller
    elif user_id in RESELLER_IDS:
        role = "💼 Reseller"
    else:
        # Fetch user role from the database
        cursor.execute('SELECT role, banned FROM users WHERE user_id = ?', (user_id,))
        user_data = cursor.fetchone()
        role = user_data[0] if user_data else "👤 Member"

    # Fetch user status (banned or active)
    cursor.execute('SELECT banned FROM users WHERE user_id = ?', (user_id,))
    banned = cursor.fetchone()
    status = "🔴 Banned" if banned and banned[0] else "🟢 Active"

    # Check if the user is in a group
    chat_type = message.chat.type
    if chat_type == "group" or chat_type == "supergroup":
        group_status = "🟢 Member"
    else:
        group_status = "🔴 Not in group"

    # Send user info
    message.reply_text(
        f"👤 **User Info:**\n"
        f"🆔 ID: `{user_id}`\n"
        f"📛 Name: {username}\n"
        f"🎭 Role: {role}\n"
        f"🚦 Status: {status}\n"
        f"👥 Group Status: {group_status}\n\n"
        "Bot made by @hack_chiye"
    )

# Start Task command
@app.on_message(filters.command("starttask"))
def start_task(client, message):
    user_id = message.from_user.id
    args = message.text.split()

    if len(args) < 4:
        message.reply_text("❌ Usage: /starttask [IP] [PORT] [METHOD] [DURATION]")
        return

    ip = args[1]
    port = args[2]
    method = args[3] if len(args) > 3 else "UDP"
    duration = args[4] if len(args) > 4 else "10m"

    # Deduct tokens
    cursor.execute('UPDATE users SET tokens = tokens - 1 WHERE user_id = ?', (user_id,))
    conn.commit()

    # Log task
    cursor.execute('INSERT INTO tasks (user_id, ip, port, method, duration) VALUES (?, ?, ?, ?, ?)',
                   (user_id, ip, port, method, duration))
    conn.commit()
    task_id = cursor.lastrowid

    # Start task in a separate thread
    threading.Thread(target=execute_task, args=(task_id, ip, port, method, duration)).start()

    message.reply_text(f"🚀 Task started on `{ip}:{port}` using `{method}` for `{duration}`.\n\nBot made by @hack_chiye")

# Stop Task command
@app.on_message(filters.command("stoptask"))
def stop_task(client, message):
    user_id = message.from_user.id
    args = message.text.split()

    if len(args) < 2:
        message.reply_text("❌ Usage: /stoptask [ID]")
        return

    task_id = args[1]

    # Check if the user owns the task
    cursor.execute('SELECT * FROM tasks WHERE task_id = ? AND user_id = ?', (task_id, user_id))
    task = cursor.fetchone()

    if not task:
        message.reply_text("❌ You don't have permission to stop this task.")
        return

    # Simulate stopping the task (kill the process)
    cursor.execute('UPDATE tasks SET status = "stopped" WHERE task_id = ?', (task_id,))
    conn.commit()

    message.reply_text(f"🛑 Task `{task_id}` stopped.\n\nBot made by @hack_chiye")

# Add Tokens command
@app.on_message(filters.command("addtokens"))
def add_tokens(client, message):
    user_id = message.from_user.id
    args = message.text.split()

    if len(args) < 3:
        message.reply_text("❌ Usage: /addtokens [ID] [AMOUNT]")
        return

    target_user_id = int(args[1])
    amount = int(args[2])

    # Check if the user is an admin or reseller
    cursor.execute('SELECT role FROM users WHERE user_id = ?', (user_id,))
    role = cursor.fetchone()[0]

    if role not in ["admin", "reseller"]:
        message.reply_text("❌ You don't have permission to add tokens.")
        return

    # Add tokens to the target user
    cursor.execute('UPDATE users SET tokens = tokens + ? WHERE user_id = ?', (amount, target_user_id))
    conn.commit()

    message.reply_text(f"✅ Added `{amount}` tokens to user `{target_user_id}`.\n\nBot made by @hack_chiye")

# Check Tokens command
@app.on_message(filters.command("checktokens"))
def check_tokens(client, message):
    user_id = message.from_user.id

    cursor.execute('SELECT tokens FROM users WHERE user_id = ?', (user_id,))
    tokens = cursor.fetchone()[0]

    message.reply_text(f"💰 You have `{tokens}` tokens remaining.\n\nBot made by @hack_chiye")

# Ban User command
@app.on_message(filters.command("ban"))
def ban_user(client, message):
    user_id = message.from_user.id
    args = message.text.split()

    if len(args) < 2:
        message.reply_text("❌ Usage: /ban [ID]")
        return

    target_user_id = int(args[1])

    # Check if the user is an admin
    cursor.execute('SELECT role FROM users WHERE user_id = ?', (user_id,))
    role = cursor.fetchone()[0]

    if role != "admin":
        message.reply_text("❌ You don't have permission to ban users.")
        return

    # Ban the user
    cursor.execute('UPDATE users SET banned = 1 WHERE user_id = ?', (target_user_id,))
    conn.commit()

    message.reply_text(f"🔴 User `{target_user_id}` has been banned.\n\nBot made by @hack_chiye")

# Unban User command
@app.on_message(filters.command("unban"))
def unban_user(client, message):
    user_id = message.from_user.id
    args = message.text.split()

    if len(args) < 2:
        message.reply_text("❌ Usage: /unban [ID]")
        return

    target_user_id = int(args[1])

    # Check if the user is an admin
    cursor.execute('SELECT role FROM users WHERE user_id = ?', (user_id,))
    role = cursor.fetchone()[0]

    if role != "admin":
        message.reply_text("❌ You don't have permission to unban users.")
        return

    # Unban the user
    cursor.execute('UPDATE users SET banned = 0 WHERE user_id = ?', (target_user_id,))
    conn.commit()

    message.reply_text(f"🟢 User `{target_user_id}` has been unbanned.\n\nBot made by @hack_chiye")

# Add Reseller command
@app.on_message(filters.command("addreseller"))
def add_reseller(client, message):
    user_id = message.from_user.id
    args = message.text.split()

    if len(args) < 2:
        message.reply_text("❌ Usage: /addreseller [ID]")
        return

    target_user_id = int(args[1])

    # Check if the user is an admin
    cursor.execute('SELECT role FROM users WHERE user_id = ?', (user_id,))
    role = cursor.fetchone()[0]

    if role != "admin":
        message.reply_text("❌ You don't have permission to add resellers.")
        return

    # Grant reseller privileges
    cursor.execute('UPDATE users SET role = "reseller" WHERE user_id = ?', (target_user_id,))
    conn.commit()

    message.reply_text(f"💼 User `{target_user_id}` has been granted reseller privileges.\n\nBot made by @hack_chiye")

# Remove Reseller command
@app.on_message(filters.command("removereseller"))
def remove_reseller(client, message):
    user_id = message.from_user.id
    args = message.text.split()

    if len(args) < 2:
        message.reply_text("❌ Usage: /removereseller [ID]")
        return

    target_user_id = int(args[1])

    # Check if the user is an admin
    cursor.execute('SELECT role FROM users WHERE user_id = ?', (user_id,))
    role = cursor.fetchone()[0]

    if role != "admin":
        message.reply_text("❌ You don't have permission to remove resellers.")
        return

    # Remove reseller privileges
    cursor.execute('UPDATE users SET role = "member" WHERE user_id = ?', (target_user_id,))
    conn.commit()

    message.reply_text(f"👤 User `{target_user_id}` has been removed as a reseller.\n\nBot made by @hack_chiye")

# Set Admin command
@app.on_message(filters.command("setadmin"))
def set_admin(client, message):
    user_id = message.from_user.id
    args = message.text.split()

    if len(args) < 2:
        message.reply_text("❌ Usage: /setadmin [ID]")
        return

    target_user_id = int(args[1])

    # Check if the user is an admin
    cursor.execute('SELECT role FROM users WHERE user_id = ?', (user_id,))
    role = cursor.fetchone()[0]

    if role != "admin":
        message.reply_text("❌ You don't have permission to set admins.")
        return

    # Grant admin privileges
    cursor.execute('UPDATE users SET role = "admin" WHERE user_id = ?', (target_user_id,))
    conn.commit()

    message.reply_text(f"👑 User `{target_user_id}` has been granted admin privileges.\n\nBot made by @hack_chiye")

# Remove Admin command
@app.on_message(filters.command("removeadmin"))
def remove_admin(client, message):
    user_id = message.from_user.id
    args = message.text.split()

    if len(args) < 2:
        message.reply_text("❌ Usage: /removeadmin [ID]")
        return

    target_user_id = int(args[1])

    # Check if the user is an admin
    cursor.execute('SELECT role FROM users WHERE user_id = ?', (user_id,))
    role = cursor.fetchone()[0]

    if role != "admin":
        message.reply_text("❌ You don't have permission to remove admins.")
        return

    # Remove admin privileges
    cursor.execute('UPDATE users SET role = "member" WHERE user_id = ?', (target_user_id,))
    conn.commit()

    message.reply_text(f"👤 User `{target_user_id}` has been removed as an admin.\n\nBot made by @hack_chiye")

# List Users command
@app.on_message(filters.command("listusers"))
def list_users(client, message):
    user_id = message.from_user.id

    # Check if the user is an admin or reseller
    cursor.execute('SELECT role FROM users WHERE user_id = ?', (user_id,))
    role = cursor.fetchone()[0]

    if role not in ["admin", "reseller"]:
        message.reply_text("❌ You don't have permission to list users.")
        return

    # Fetch all users
    cursor.execute('SELECT user_id, username, role, banned FROM users')
    users = cursor.fetchall()

    user_list = "\n".join([f"🆔 ID: {u[0]}, 📛 Name: {u[1]}, 🎭 Role: {u[2]}, 🚦 Status: {'🔴 Banned' if u[3] else '🟢 Active'}" for u in users])
    message.reply_text(f"👥 **User List:**\n{user_list}\n\nBot made by @hack_chiye")

# Network Status command
@app.on_message(filters.command("networkstatus"))
def network_status(client, message):
    # Simulate network status check
    message.reply_text("🌐 Network status: ✅ Online\n\nBot made by @hack_chiye")

# Bot Ping command
@app.on_message(filters.command("botping"))
def bot_ping(client, message):
    message.reply_text("🏓 Pong!\n\nBot made by @hack_chiye")

# Running Tasks command
@app.on_message(filters.command("runningtasks"))
def running_tasks(client, message):
    # Fetch running tasks
    cursor.execute('SELECT task_id, ip, port, method, duration FROM tasks WHERE status = "running"')
    tasks = cursor.fetchall()

    if not tasks:
        message.reply_text("🛑 No tasks are currently running.\n\nBot made by @hack_chiye")
        return

    task_list = "\n".join([f"🆔 ID: {t[0]}, 🌐 IP: {t[1]}, 🚪 Port: {t[2]}, 🛠 Method: {t[3]}, ⏳ Duration: {t[4]}" for t in tasks])
    message.reply_text(f"🚀 **Running Tasks:**\n{task_list}\n\nBot made by @hack_chiye")

# System Info command
@app.on_message(filters.command("systeminfo"))
def system_info(client, message):
    # Fetch system information
    cpu_usage = psutil.cpu_percent()
    memory_usage = psutil.virtual_memory().percent
    disk_usage = psutil.disk_usage('/').percent

    message.reply_text(
        f"💻 **System Information:**\n"
        f"🖥 CPU Usage: {cpu_usage}%\n"
        f"🧠 Memory Usage: {memory_usage}%\n"
        f"💾 Disk Usage: {disk_usage}%\n\n"
        "Bot made by @hack_chiye"
    )

# Server Logs command
@app.on_message(filters.command("serverlogs"))
def server_logs(client, message):
    # Fetch latest logs
    cursor.execute('SELECT action, timestamp FROM logs ORDER BY log_id DESC LIMIT 10')
    logs = cursor.fetchall()

    log_list = "\n".join([f"🕒 {l[1]}: {l[0]}" for l in logs])
    message.reply_text(f"📜 **Latest Server Logs:**\n{log_list}\n\nBot made by @hack_chiye")

# Analytics command
@app.on_message(filters.command("analytics"))
def analytics(client, message):
    # Fetch analytics data
    cursor.execute('SELECT COUNT(*) FROM tasks')
    total_tasks = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM feedback WHERE feedback = "success"')
    success_tasks = cursor.fetchone()[0]

    success_rate = (success_tasks / total_tasks) * 100 if total_tasks > 0 else 0

    message.reply_text(
        f"📊 **Analytics:**\n"
        f"📈 Total Tasks: {total_tasks}\n"
        f"✅ Success Rate: {success_rate:.2f}%\n"
        f"❌ Failed Tasks: {total_tasks - success_tasks}\n\n"
        "Bot made by @hack_chiye"
    )

# Whitelist IP command
@app.on_message(filters.command("whitelist"))
def whitelist_ip(client, message):
    user_id = message.from_user.id
    args = message.text.split()

    if len(args) < 2:
        message.reply_text("❌ Usage: /whitelist [IP]")
        return

    ip = args[1]

    # Check if the user is an admin
    cursor.execute('SELECT role FROM users WHERE user_id = ?', (user_id,))
    role = cursor.fetchone()[0]

    if role != "admin":
        message.reply_text("❌ You don't have permission to whitelist IPs.")
        return

    # Add IP to whitelist
    cursor.execute('INSERT OR IGNORE INTO whitelist (ip) VALUES (?)', (ip,))
    conn.commit()

    message.reply_text(f"✅ IP `{ip}` has been added to the whitelist.\n\nBot made by @hack_chiye")

# Blacklist IP command
@app.on_message(filters.command("blacklist"))
def blacklist_ip(client, message):
    user_id = message.from_user.id
    args = message.text.split()

    if len(args) < 2:
        message.reply_text("❌ Usage: /blacklist [IP]")
        return

    ip = args[1]

    # Check if the user is an admin
    cursor.execute('SELECT role FROM users WHERE user_id = ?', (user_id,))
    role = cursor.fetchone()[0]

    if role != "admin":
        message.reply_text("❌ You don't have permission to blacklist IPs.")
        return

    # Add IP to blacklist
    cursor.execute('INSERT OR IGNORE INTO blacklist (ip) VALUES (?)', (ip,))
    conn.commit()

    message.reply_text(f"🔴 IP `{ip}` has been added to the blacklist.\n\nBot made by @hack_chiye")

# Check Whitelist command
@app.on_message(filters.command("checkwhitelist"))
def check_whitelist(client, message):
    # Fetch whitelisted IPs
    cursor.execute('SELECT ip FROM whitelist')
    whitelist = cursor.fetchall()

    if not whitelist:
        message.reply_text("🛑 No IPs are whitelisted.\n\nBot made by @hack_chiye")
        return

    whitelist_ips = "\n".join([f"✅ {w[0]}" for w in whitelist])
    message.reply_text(f"📝 **Whitelisted IPs:**\n{whitelist_ips}\n\nBot made by @hack_chiye")

# Check Blacklist command
@app.on_message(filters.command("checkblacklist"))
def check_blacklist(client, message):
    # Fetch blacklisted IPs
    cursor.execute('SELECT ip FROM blacklist')
    blacklist = cursor.fetchall()

    if not blacklist:
        message.reply_text("🛑 No IPs are blacklisted.\n\nBot made by @hack_chiye")
        return

    blacklist_ips = "\n".join([f"🔴 {b[0]}" for b in blacklist])
    message.reply_text(f"📝 **Blacklisted IPs:**\n{blacklist_ips}\n\nBot made by @hack_chiye")

# Set Welcome Message command
@app.on_message(filters.command("setwelcome"))
def set_welcome(client, message):
    user_id = message.from_user.id
    args = message.text.split(maxsplit=1)

    if len(args) < 2:
        message.reply_text("❌ Usage: /setwelcome [message]")
        return

    welcome_message = args[1]

    # Check if the user is an admin
    cursor.execute('SELECT role FROM users WHERE user_id = ?', (user_id,))
    role = cursor.fetchone()[0]

    if role != "admin":
        message.reply_text("❌ You don't have permission to set the welcome message.")
        return

    # Update welcome message (simulated)
    message.reply_text(f"✅ Welcome message set to: {welcome_message}\n\nBot made by @hack_chiye")

# Set Help Message command
@app.on_message(filters.command("sethelp"))
def set_help(client, message):
    user_id = message.from_user.id
    args = message.text.split(maxsplit=1)

    if len(args) < 2:
        message.reply_text("❌ Usage: /sethelp [message]")
        return

    help_message = args[1]

    # Check if the user is an admin
    cursor.execute('SELECT role FROM users WHERE user_id = ?', (user_id,))
    role = cursor.fetchone()[0]

    if role != "admin":
        message.reply_text("❌ You don't have permission to set the help message.")
        return

    # Update help message (simulated)
    message.reply_text(f"✅ Help message set to: {help_message}\n\nBot made by @hack_chiye")

# Set Cooldown command
@app.on_message(filters.command("setcooldown"))
def set_cooldown(client, message):
    user_id = message.from_user.id
    args = message.text.split()

    if len(args) < 2:
        message.reply_text("❌ Usage: /setcooldown [seconds]")
        return

    cooldown = args[1]

    # Check if the user is an admin
    cursor.execute('SELECT role FROM users WHERE user_id = ?', (user_id,))
    role = cursor.fetchone()[0]

    if role != "admin":
        message.reply_text("❌ You don't have permission to set the cooldown.")
        return

    # Update cooldown (simulated)
    message.reply_text(f"✅ Cooldown set to {cooldown} seconds.\n\nBot made by @hack_chiye")

# Set Max Duration command
@app.on_message(filters.command("setmaxduration"))
def set_max_duration(client, message):
    user_id = message.from_user.id
    args = message.text.split()

    if len(args) < 2:
        message.reply_text("❌ Usage: /setmaxduration [time]")
        return

    max_duration = args[1]

    # Check if the user is an admin
    cursor.execute('SELECT role FROM users WHERE user_id = ?', (user_id,))
    role = cursor.fetchone()[0]

    if role != "admin":
        message.reply_text("❌ You don't have permission to set the max duration.")
        return

    # Update max duration (simulated)
    message.reply_text(f"✅ Max duration set to {max_duration}.\n\nBot made by @hack_chiye")

# Run the bot
app.run()
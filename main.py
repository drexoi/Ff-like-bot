import os
import json
import time
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8822768029:AAF1UoUMhrqtbm36EVkKC1vV1qyn8vgRAFo"
ADMIN_ID = 8671410379
UPI_ID = "Oxrehan11@oksbi"
FF_LIKE_URL = "https://client.ind.freefiremobile.com/LikeProfile"

bot = telebot.TeleBot(BOT_TOKEN)

CHANNELS = [
    {"chat_id": "@Ox1MODS", "url": "https://t.me/Ox1MODS", "name": "Channel 1"},
    {"chat_id": "@Ox2MODS", "url": "https://t.me/Ox2MODS", "name": "Channel 2"},
    {"chat_id": "@OxRehanCyber", "url": "https://t.me/OxRehanCyber", "name": "Channel 3"},
    {"chat_id": -1003782903063, "url": "https://t.me/+fw4X2NYNRmoyODA1", "name": "Channel 4"}
]

PACKS = {
    "pack_20": {"price": 20, "credits": 50, "likes": 150},
    "pack_50": {"price": 50, "credits": 150, "likes": 450},
    "pack_100": {"price": 100, "credits": 350, "likes": 1050},
    "pack_250": {"price": 250, "credits": 1000, "likes": 3000}
}

DATA_FILE = "bot_data.json"
PENDING_PAYMENTS = {}
USER_STEPS = {}

def load_data():
    default_data = {"users": {}, "redeem_codes": {}}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return default_data
    return default_data

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_all_accounts():
    accounts = []
    seen_ids = set()
    for file in os.listdir('.'):
        if file.endswith('.json') and file not in ['localconfig.json', 'package.json', DATA_FILE]:
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
        markup.add(InlineKeyboardButton(text=f"📢 Join {ch['name']}", url=ch["url"]))
    markup.add(InlineKeyboardButton(text="✅ Joined / Verify", callback_data="verify_join"))
    return markup

def main_menu_markup():
    markup = InlineKeyboardMarkup(row_width=2)
    b1 = InlineKeyboardButton(text="👍 Get Likes", callback_data="btn_get_likes")
    b2 = InlineKeyboardButton(text="💳 Buy Credits", callback_data="btn_buy_credits")
    b3 = InlineKeyboardButton(text="💰 My Balance", callback_data="btn_balance")
    b4 = InlineKeyboardButton(text="🔗 Invite & Earn", callback_data="btn_refer")
    b5 = InlineKeyboardButton(text="🎁 Redeem Code", callback_data="btn_redeem")
    markup.add(b1)
    markup.add(b2, b3)
    markup.add(b4, b5)
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
        if response.status_code == 200:
            return True
        return False
    except Exception:
        return False

@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = str(message.from_user.id)
    data = load_data()
    args = message.text.split()
    referrer_id = None

    if len(args) > 1 and args[1].startswith("ref_"):
        ref_candidate = args[1].replace("ref_", "").strip()
        if ref_candidate != user_id:
            referrer_id = ref_candidate

    if user_id not in data["users"]:
        data["users"][user_id] = {
            "credits": 10,
            "referred_by": referrer_id,
            "verified": False,
            "ref_reward_given": False
        }
        save_data(data)

    if not check_force_join(int(user_id)):
        text = (
            "⚠️ *Must Join Our Channels First!*\n\n"
            "Join all 4 channels below to unlock the bot and claim your free credits."
        )
        bot.send_message(message.chat.id, text, reply_markup=force_join_markup(), parse_mode="Markdown")
        return

    complete_verification(int(user_id), message.chat.id)

def complete_verification(user_id, chat_id):
    user_id_str = str(user_id)
    data = load_data()
    user_info = data["users"].get(user_id_str, {"credits": 10, "verified": True, "ref_reward_given": False})
    user_info["verified"] = True

    if user_info.get("referred_by") and not user_info.get("ref_reward_given"):
        ref_id = user_info["referred_by"]
        if ref_id in data["users"]:
            data["users"][ref_id]["credits"] += 10
            user_info["ref_reward_given"] = True
            try:
                bot.send_message(
                    int(ref_id),
                    "🎉 *Referral Bonus Received!*\nYour friend joined all channels. You earned *10 Credits*!",
                    parse_mode="Markdown"
                )
            except Exception:
                pass

    data["users"][user_id_str] = user_info
    save_data(data)

    text = (
        "🔥 *Welcome to Free Fire Like Dispatcher* 🔥\n\n"
        f"⚡ *Loaded Bot Nodes:* `{len(BOT_ACCOUNTS)}`\n"
        f"💰 *Your Balance:* `{user_info['credits']} Credits`\n"
        f"📊 *Rate:* `1 Credit = 3 Likes`\n\n"
        "Select an option below to proceed:"
    )
    bot.send_message(chat_id, text, reply_markup=main_menu_markup(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "verify_join")
def verify_callback(call):
    user_id = call.from_user.id
    if check_force_join(user_id):
        bot.answer_callback_query(call.id, "✅ Channels verified!")
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        complete_verification(user_id, call.message.chat.id)
    else:
        bot.answer_callback_query(call.id, "❌ Please join all channels before verifying!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "btn_balance")
def balance_callback(call):
    user_id = str(call.from_user.id)
    data = load_data()
    credits_amt = data["users"].get(user_id, {}).get("credits", 0)
    bot.answer_callback_query(call.id)
    text = (
        f"💳 *Your Account Balance*\n\n"
        f"Available Credits: *{credits_amt}*\n"
        f"Available Likes: *{credits_amt * 3} Likes*"
    )
    bot.send_message(call.message.chat.id, text, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "btn_refer")
def refer_callback(call):
    user_id = call.from_user.id
    bot_info = bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"
    bot.answer_callback_query(call.id)
    text = (
        "🔗 *Invite & Earn Free Credits*\n\n"
        "Share your referral link with friends. When they start the bot and join all 4 channels, you will get *10 Credits* instantly!\n\n"
        f"Your Referral Link:\n`{ref_link}`"
    )
    bot.send_message(call.message.chat.id, text, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "btn_redeem")
def redeem_callback(call):
    bot.answer_callback_query(call.id)
    USER_STEPS[call.from_user.id] = {"step": "awaiting_redeem_code"}
    bot.send_message(call.message.chat.id, "🎁 Please send your Redeem Code:")

@bot.callback_query_handler(func=lambda call: call.data == "btn_buy_credits")
def buy_callback(call):
    bot.answer_callback_query(call.id)
    markup = InlineKeyboardMarkup()
    for key, val in PACKS.items():
        btn_text = f"₹{val['price']} ➔ {val['credits']} Credits ({val['likes']} Likes)"
        markup.add(InlineKeyboardButton(text=btn_text, callback_data=f"buy_{key}"))
    bot.send_message(call.message.chat.id, "🛒 *Select a Credit Pack:*", reply_markup=markup, parse_mode="Markdown")

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
        f"💳 *Order Summary*\n\n"
        f"Amount to Pay: *₹{price}*\n"
        f"Credits Allocated: *{credits_amt} Credits*\n"
        f"UPI ID: `{UPI_ID}`\n\n"
        "Scan the QR code above or pay directly to the UPI ID.\n"
        "⚠️ *After payment, send the screenshot of the payment receipt here.*"
    )

    try:
        bot.send_photo(call.message.chat.id, qr_url, caption=caption, parse_mode="Markdown")
    except Exception:
        bot.send_message(call.message.chat.id, caption, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "btn_get_likes")
def get_likes_callback(call):
    user_id = call.from_user.id
    if not check_force_join(user_id):
        bot.answer_callback_query(call.id, "Please join all channels first!", show_alert=True)
        bot.send_message(call.message.chat.id, "Join our channels:", reply_markup=force_join_markup())
        return

    bot.answer_callback_query(call.id)
    USER_STEPS[user_id] = {"step": "awaiting_uid"}
    bot.send_message(call.message.chat.id, "🎯 Please enter your Free Fire Player UID:")

@bot.message_handler(content_types=['photo'])
def handle_payment_screenshot(message):
    user_id = message.from_user.id
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
            f"🔔 *New Payment Proof Received!*\n\n"
            f"From User: `{user_id}` (@{message.from_user.username})\n"
            f"Expected Amount: *₹{price}*\n"
            f"Credits to Add: *{credits_amt}*"
        )

        bot.send_photo(ADMIN_ID, file_id, caption=admin_caption, reply_markup=admin_markup, parse_mode="Markdown")
        bot.reply_to(message, "✅ Screenshot submitted to admin for verification. Your credits will be added once approved.")
        pending["awaiting_proof"] = False

@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_app_"))
def admin_approve_payment(call):
    if call.from_user.id != ADMIN_ID:
        return
    parts = call.data.split("_")
    target_user_id = parts[2]
    credits_to_add = int(parts[3])

    data = load_data()
    if target_user_id in data["users"]:
        data["users"][target_user_id]["credits"] += credits_to_add
    else:
        data["users"][target_user_id] = {"credits": credits_to_add, "verified": True, "ref_reward_given": False}
    save_data(data)

    bot.answer_callback_query(call.id, "Approved!")
    bot.edit_message_caption(
        caption=call.message.caption + "\n\n🟢 *STATUS: APPROVED BY ADMIN*",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id
    )

    try:
        bot.send_message(
            int(target_user_id),
            f"🎉 *Payment Approved!*\n*{credits_to_add} Credits* have been added to your balance.",
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
            "❌ *Payment Verification Failed!*\nYour receipt was rejected by admin. Please contact support.",
            parse_mode="Markdown"
        )
    except Exception:
        pass

@bot.message_handler(func=lambda m: m.text and not m.text.startswith('/'))
def handle_text_steps(message):
    user_id = message.from_user.id
    text = message.text.strip()
    step_info = USER_STEPS.get(user_id)

    if not step_info:
        return

    current_step = step_info.get("step")

    if current_step == "awaiting_uid":
        if not text.isdigit():
            bot.reply_to(message, "❌ Invalid UID! UID must contain only numbers. Try again:")
            return

        step_info["target_uid"] = text
        step_info["step"] = "awaiting_like_amount"
        USER_STEPS[user_id] = step_info

        data = load_data()
        user_credits = data["users"].get(str(user_id), {}).get("credits", 0)

        prompt = (
            f"🎯 Target UID: `{text}`\n"
            f"💰 Your Balance: *{user_credits} Credits*\n"
            f"📊 Rate: *1 Credit = 3 Likes*\n\n"
            "How many likes do you want to send?"
        )
        bot.send_message(message.chat.id, prompt, parse_mode="Markdown")

    elif current_step == "awaiting_like_amount":
        if not text.isdigit() or int(text) <= 0:
            bot.reply_to(message, "❌ Please enter a valid positive number for likes:")
            return

        likes_requested = int(text)
        required_credits = (likes_requested + 2) // 3

        data = load_data()
        user_id_str = str(user_id)
        user_credits = data["users"].get(user_id_str, {}).get("credits", 0)

        if user_credits < required_credits:
            del USER_STEPS[user_id]
            err_msg = (
                f"❌ *Insufficient Credits!*\n\n"
                f"Likes requested: *{likes_requested}*\n"
                f"Required credits: *{required_credits} Credits*\n"
                f"Your balance: *{user_credits} Credits*\n\n"
                "Please buy credits or refer friends to continue."
            )
            bot.send_message(message.chat.id, err_msg, reply_markup=main_menu_markup(), parse_mode="Markdown")
            return

        data["users"][user_id_str]["credits"] -= required_credits
        save_data(data)

        target_uid = step_info.get("target_uid")
        del USER_STEPS[user_id]

        status_msg = bot.send_message(
            message.chat.id,
            f"🚀 *Sending {likes_requested} likes to UID: `{target_uid}`...*",
            parse_mode="Markdown"
        )

        dispatch_accounts = BOT_ACCOUNTS[:likes_requested]
        success_count = 0
        fail_count = 0

        for acc in dispatch_accounts:
            if send_like_request(acc, target_uid):
                success_count += 1
            else:
                fail_count += 1
            time.sleep(0.04)

        final_text = (
            f"✅ *Mission Completed!*\n\n"
            f"🎯 Target UID: `{target_uid}`\n"
            f"👍 Likes Sent: *{success_count}*\n"
            f"⚠️ Failed: *{fail_count}*\n"
            f"💳 Deducted: *{required_credits} Credits*\n"
            f"💰 Remaining: *{data['users'][user_id_str]['credits']} Credits*"
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
        data = load_data()
        user_id_str = str(user_id)

        if code not in data.get("redeem_codes", {}):
            bot.reply_to(message, "❌ Invalid or expired redeem code.")
            return

        code_info = data["redeem_codes"][code]
        if code_info["uses_left"] <= 0:
            bot.reply_to(message, "❌ This redeem code has already reached its maximum limit.")
            return

        if user_id_str in code_info["claimed_by"]:
            bot.reply_to(message, "⚠️ You have already redeemed this code.")
            return

        credits_reward = code_info["credits"]
        code_info["uses_left"] -= 1
        code_info["claimed_by"].append(user_id_str)

        if user_id_str not in data["users"]:
            data["users"][user_id_str] = {"credits": 0, "verified": True, "ref_reward_given": False}

        data["users"][user_id_str]["credits"] += credits_reward
        save_data(data)

        bot.reply_to(
            message,
            f"🎉 *Code Redeemed Successfully!*\n*{credits_reward} Credits* added to your account.\nNew Balance: *{data['users'][user_id_str]['credits']} Credits*",
            parse_mode="Markdown"
        )

@bot.message_handler(commands=['gen'])
def admin_generate_code(message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) < 4:
        bot.reply_to(message, "Usage: `/gen <CODE_NAME> <CREDITS> <MAX_USERS>`\nExample: `/gen VIP500 500 5`", parse_mode="Markdown")
        return

    code_name = args[1].upper()
    try:
        credits_amt = int(args[2])
        max_uses = int(args[3])
    except ValueError:
        bot.reply_to(message, "Credits and Users count must be integers.")
        return

    data = load_data()
    data["redeem_codes"][code_name] = {
        "credits": credits_amt,
        "uses_left": max_uses,
        "claimed_by": []
    }
    save_data(data)

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

    data = load_data()
    if target_id not in data["users"]:
        data["users"][target_id] = {"credits": 0, "verified": True, "ref_reward_given": False}
    data["users"][target_id]["credits"] += amount
    save_data(data)

    bot.reply_to(message, f"✅ Added {amount} credits to `{target_id}`.")
    try:
        bot.send_message(int(target_id), f"🎉 Admin added *{amount} Credits* to your balance!", parse_mode="Markdown")
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

    data = load_data()
    if target_id in data["users"]:
        data["users"][target_id]["credits"] = max(0, data["users"][target_id]["credits"] - amount)
        save_data(data)
        bot.reply_to(message, f"✅ Deducted {amount} credits from `{target_id}`.")

@bot.message_handler(commands=['broadcast'])
def admin_broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return
    msg_text = message.text.replace('/broadcast', '').strip()
    if not msg_text:
        bot.reply_to(message, "Usage: `/broadcast Your message here`")
        return

    data = load_data()
    users = list(data["users"].keys())
    sent = 0
    for uid in users:
        try:
            bot.send_message(int(uid), msg_text)
            sent += 1
            time.sleep(0.04)
        except Exception:
            pass
    bot.reply_to(message, f"📢 Broadcast finished: Sent to {sent}/{len(users)} users.")

@bot.message_handler(commands=['stats'])
def admin_stats(message):
    if message.from_user.id != ADMIN_ID:
        return
    data = load_data()
    total_users = len(data["users"])
    total_active_codes = len([c for c in data.get("redeem_codes", {}).values() if c["uses_left"] > 0])
    bot.reply_to(
        message,
        f"📊 *Bot Statistics*\n\n"
        f"👥 Total Users: `{total_users}`\n"
        f"🤖 Available Bot Nodes: `{len(BOT_ACCOUNTS)}`\n"
        f"🎁 Active Redeem Codes: `{total_active_codes}`",
        parse_mode="Markdown"
    )

if __name__ == "__main__":
    print("Bot polling started...")
    bot.infinity_polling()

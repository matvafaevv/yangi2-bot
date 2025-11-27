import requests
import time
import random

BOT_TOKEN = "8536756798:AAHaXa_Zrxu3htBVI-P_jhn6SPyDCpgbeOg"
ADMIN_ID = 6365371142
CHANNEL_ID = -1003422486517  # Kanal ID

API = f"https://api.telegram.org/bot{BOT_TOKEN}/"

bot_state = {
    "random_active": False,
    "total_users_needed": 0,
    "winners_count": 0,
    "collected": []
}

admin_step = {}
admin_temp = {}

# ------------------- Helper Functions -------------------

def send_message(chat_id, text, reply_markup=None, parse_mode=None):
    data = {"chat_id": chat_id, "text": text}
    if reply_markup:
        data["reply_markup"] = reply_markup
    if parse_mode:
        data["parse_mode"] = parse_mode
    try:
        requests.post(API + "sendMessage", json=data, timeout=5)
    except:
        pass

def send_photo(chat_id, photo_file_id, caption=None, reply_markup=None):
    data = {"chat_id": chat_id, "photo": photo_file_id}
    if caption:
        data["caption"] = caption
    if reply_markup:
        data["reply_markup"] = reply_markup
    try:
        requests.post(API + "sendPhoto", json=data, timeout=10)
    except:
        pass

def get_updates(offset=None):
    params = {"timeout": 30}
    if offset:
        params["offset"] = offset
    try:
        return requests.get(API + "getUpdates", params=params, timeout=35).json()
    except:
        return {"result": []}

def keyboard_yes_no():
    return {"inline_keyboard": [[{"text": "Ha", "callback_data": "yes"}],
                                [{"text": "Yo'q", "callback_data": "no"}]]}

def keyboard_confirm():
    return {"inline_keyboard": [[{"text": "Randomni boshlash", "callback_data": "confirm"}]]}

# ------------------- Random Functions -------------------

def finish_random():
    users = bot_state["collected"]
    winners_count = bot_state["winners_count"]

    if len(users) == 0:
        send_message(ADMIN_ID, "❌ Hech kim ishtirok etmadi.")
        bot_state["random_active"] = False
        return

    winners = random.sample(users, winners_count)
    result = "🎉 RANDOM NATIJALARI\n\n"
    result += f"G‘oliblar soni: {winners_count} ta\n\n"

    # Har bir g‘olib ismi ustiga bosilsa profilga kirishi
    for i, w in enumerate(winners, 1):
        user_info = w["from"]
        display_name = user_info.get("first_name", "Ishtirokchi")
        user_id = user_info["id"]
        result += f"{i}. [{display_name}](tg://user?id={user_id}) — ID: {w['id']}\n"

    # Markdown parse_mode bilan yuborish
    send_message(CHANNEL_ID, result, parse_mode="Markdown")
    send_message(ADMIN_ID, "🎉 G‘oliblar kanalga yuborildi!")

    bot_state["random_active"] = False
    bot_state["collected"] = []
    bot_state["total_users_needed"] = 0
    bot_state["winners_count"] = 0

def stop_random():
    bot_state["random_active"] = False
    bot_state["collected"] = []
    send_message(ADMIN_ID, "⛔ Random majburan to‘xtatildi!")

def process_admin_message(uid, text):
    step = admin_step.get(uid)

    # Random boshqarish qismi
    if step == "total":
        if not text.isdigit():
            send_message(uid, "Faqat raqam kiriting!")
            return
        bot_state["total_users_needed"] = int(text)
        admin_step[uid] = "winners"
        send_message(uid, "Nechi g‘olib bo‘ladi?")
        return
    if step == "winners":
        if not text.isdigit():
            send_message(uid, "Faqat raqam kiriting!")
            return
        count = int(text)
        if count <= 0 or count > bot_state["total_users_needed"]:
            send_message(uid, f"G‘oliblar soni 1 dan {bot_state['total_users_needed']} gacha bo‘lsin!")
            return
        bot_state["winners_count"] = count
        admin_step[uid] = None
        send_message(uid, "Random tayyor! Boshlash uchun 'Randomni boshlash' tugmasini bosing.", reply_markup=keyboard_confirm())
        return

    # /xabar bosilganidan keyin matn qabul qilish
    if step == "send_text":
        admin_temp[uid]["caption"] = text
        admin_step[uid] = "ready_to_send"
        file_id = admin_temp[uid].get("photo_file_id")
        caption = admin_temp[uid].get("caption", "")
        send_photo(ADMIN_ID, file_id, caption=caption)
        send_message(ADMIN_ID, "Hammasi tayyor. Kanalga yuborish uchun /send ni yuboring.")
        return

# ------------------- User ID Processing -------------------

def process_user_id(msg):
    if not bot_state["random_active"]:
        send_message(msg["from"]["id"], "Random hozir ochiq emas!")
        return
    text = msg.get("text", "").strip()
    if not text.isdigit() or len(text) != 10:
        send_message(msg["from"]["id"], "❌ 10 xonali ID yuboring!")
        return
    if any(u["id"] == text for u in bot_state["collected"]):
        send_message(msg["from"]["id"], "Bu ID allaqachon kiritilgan!")
        return
    bot_state["collected"].append({"id": text, "from": msg["from"]})
    send_message(msg["from"]["id"], "✅ ID qabul qilindi!")
    remaining = bot_state["total_users_needed"] - len(bot_state["collected"])
    send_message(ADMIN_ID, f"Yangi ID: {text}\nQolgan: {remaining} ta")
    if len(bot_state["collected"]) >= bot_state["total_users_needed"]:
        finish_random()

# ------------------- Chotal Functions -------------------

def handle_admin_photo(uid, photo_list):
    largest = sorted(photo_list, key=lambda x: x.get("file_size", 0))[-1]
    file_id = largest.get("file_id")
    admin_temp[uid] = {"photo_file_id": file_id}
    admin_step[uid] = "send_text"
    send_message(uid, "Rasm qabul qilindi. Endi chotal uchun matn yuboring (caption).")

def perform_channel_send_from_admin(uid):
    temp = admin_temp.get(uid)
    if not temp:
        send_message(uid, "Hech narsa topilmadi. /xabar jarayonini yana boshlang.")
        admin_step[uid] = None
        return
    photo_file_id = temp.get("photo_file_id")
    caption = temp.get("caption", "")
    keyboard = {"inline_keyboard": [[{"text": "Qatnashish", "url": "https://t.me/assalomuqqbot?start=join"}]]}
    send_photo(CHANNEL_ID, photo_file_id, caption=caption, reply_markup=keyboard)
    send_message(ADMIN_ID, "✅ Xabar kanalga yuborildi.")
    admin_step[uid] = None
    admin_temp.pop(uid, None)

# ------------------- Main Loop -------------------

def main():
    print("Bot ishlayapti...")
    offset = None
    while True:
        try:
            updates = get_updates(offset)
            if "result" in updates:
                for update in updates["result"]:
                    offset = update["update_id"] + 1

                    if "callback_query" in update:
                        cq = update["callback_query"]
                        data = cq["data"]
                        uid = cq["from"]["id"]
                        if uid != ADMIN_ID:
                            send_message(uid, "Siz admin emassiz!")
                            continue
                        if data == "yes":
                            admin_step[uid] = "total"
                            send_message(uid, "Necha ID qabul qilinsin?")
                        elif data == "no":
                            send_message(uid, "Bekor qilindi.")
                        elif data == "confirm":
                            bot_state["random_active"] = True
                            send_message(uid, "🎉 Random boshlandi!")
                        continue

                    if "message" in update:
                        msg = update["message"]
                        uid = msg["from"]["id"]
                        text = msg.get("text", "")

                        # /start
                        if text.startswith("/start"):
                            if bot_state["random_active"]:
                                send_message(uid, "Random ochiq! 10 xonali ID yuboring.")
                            else:
                                send_message(uid, "Random hozir ochiq emas.")
                            continue

                        # Admin commands
                        if uid == ADMIN_ID:
                            if text.startswith("/admin"):
                                send_message(uid, "Random boshlansinmi?", reply_markup=keyboard_yes_no())
                                continue
                            if text.startswith("/stop"):
                                stop_random()
                                continue
                            if text.startswith("/xabar"):
                                admin_step[uid] = "send_photo"
                                admin_temp.pop(uid, None)
                                send_message(uid, "Chotal uchun rasm yuboring (photo formatda).")
                                continue
                            if text.startswith("/send"):
                                perform_channel_send_from_admin(uid)
                                continue
                            if admin_step.get(uid) in ["total", "winners", "send_text"]:
                                process_admin_message(uid, text)
                                continue

                        # User ID
                        if text.isdigit():
                            process_user_id(msg)

                        # Admin photo
                        if "photo" in msg and uid == ADMIN_ID and admin_step.get(uid) == "send_photo":
                            handle_admin_photo(uid, msg["photo"])
                            continue

        except Exception as e:
            print("Xatolik:", e)
            time.sleep(1)

if __name__ == "__main__":
    main()

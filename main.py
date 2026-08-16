import os
import re
import asyncio
import subprocess
from threading import Thread
from datetime import datetime
from flask import Flask
import pymongo
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters as tg_filters
)
from pyrogram import Client, filters

# ----------------- FLASK SERVER (KEEP-ALIVE) -----------------
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "DKLR Show Hub Engine Active!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

keep_alive()

# ----------------- CONFIG & DB -----------------
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8658926437:AAHnzF23ypbzIbZ-yATBhA0MHFGVOhVsTzA")
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://deepakkumar451811_db_user:z0gBb13CSvYAECgG@cluster0.osysn1c.mongodb.net/?appName=Cluster0")
API_ID = int(os.environ.get("API_ID", "30366893"))
API_HASH = os.environ.get("API_HASH", "ecb01a29588b13c36c8c373584270ea8")
SESSION_STRING = os.environ.get("SESSION_STRING", "")
OWNER_USERNAME = "dklr145"

client = pymongo.MongoClient(MONGO_URI)
db = client["dklr_bot_db"]
video_col = db["videos"]
shows_col = db["custom_shows"]
ott_col = db["custom_otts"]
settings_col = db["bot_settings"]

pyrogram_userbot = None
tg_bot_app = None

WATERMARK_KEYWORDS = [
    "tvshowhub", "antoni", "webdlbot", "dg_contents", "dg_content",
    "utsavtv", "nx-drm-dl", "ds_ottwebdlbot", "kairax007", "ottwebdlbot",
    "dklr_dr", "dklrdr"
]

def has_watermark(text):
    if not text:
        return False
    text_lower = text.lower()
    return any(k in text_lower for k in WATERMARK_KEYWORDS)

def get_bot_settings():
    settings = settings_col.find_one({"_id": "config"})
    if not settings:
        settings = {
            "_id": "config",
            "auto_receive": True,
            "auto_send": True,
            "source_channel_id": None,
            "source_channel_name": "Not Set",
            "target_channel_id": None,
            "target_channel_name": "Not Set",
            "admin_chat_id": None
        }
        settings_col.insert_one(settings)
    return settings

def update_bot_setting(key, value):
    settings_col.update_one({"_id": "config"}, {"$set": {key: value}}, upsert=True)

DEFAULT_OTTS = [
    ("SunNXT", "sunnxt_p1"),
    ("Zee5", "zee5_p1"),
    ("DangalPlay", "dangal_p1"),
    ("Hotstar(StarPlus & Colors)", "hotstar_p1"),
    ("SonyLiv", "sonyliv_p1")
]

DEFAULT_SHOWS = {
    "shivmay_shravan": {"name": "Shivmay Shravan", "ott": "hotstar_p1"},
    "binddii": {"name": "Binddii", "ott": "hotstar_p1"},
    "oh_humnava": {"name": "Oh Humnava - Tum Dena Saath Mera", "ott": "hotstar_p1"},
    "bareilly": {"name": "Bareilly Ke Bacchan", "ott": "hotstar_p1"},
    "juliet": {"name": "Tuu Juliet Jatt Di", "ott": "hotstar_p1"},
    "mahadev": {"name": "Mahadev & Sons", "ott": "hotstar_p1"},
    "juhi_mui": {"name": "Juhi Mui", "ott": "hotstar_p1"},
    "do_duniya": {"name": "Do Duniya Ek Dil", "ott": "hotstar_p1"},
    "parshuram": {"name": "Mr and Mrs Parshuram", "ott": "hotstar_p1"},
    "anupama": {"name": "Anupama", "ott": "hotstar_p1"},
    "yrkkh": {"name": "Yeh Rishta Kya Kehlata Hai", "ott": "hotstar_p1"},
    "sairaab": {"name": "Sairaab", "ott": "hotstar_p1"},
    "mannat": {"name": "Mannat - Har Khushi Paane Ki", "ott": "hotstar_p1"},
    "seher": {"name": "Seher Hone Ko Hai", "ott": "hotstar_p1"},
    "aarambhi": {"name": "Dr Aarambhi", "ott": "hotstar_p1"},
    "udne_ki_aasha": {"name": "Udne Ki Aasha", "ott": "hotstar_p1"},
    "kyunki_saas": {"name": "Kyunki Saas Bhi Kabhi Bahu Thi", "ott": "hotstar_p1"},
    "kyunki_rishton": {"name": "Kyunki Rishton Ke Bhi Roop Badalte Hain", "ott": "hotstar_p1"},
    "fevicreate": {"name": "Fevicreate Idea Labs", "ott": "hotstar_p1"},
    "laughter_chefs": {"name": "Laughter Chefs Unlimited Entertainment", "ott": "hotstar_p1"},
    "tu_hi_re": {"name": "Tu Hi Re Dil Mein", "ott": "zee5_p1"},
    "lakshmi_nivas": {"name": "Lakshmi Nivas", "ott": "zee5_p1"},
    "tumm_se_tumm": {"name": "Tumm Se Tumm Tak", "ott": "zee5_p1"},
    "ganga_mai": {"name": "Ganga Mai Ki Betiyan", "ott": "zee5_p1"},
    "vasudha": {"name": "Vasudha", "ott": "zee5_p1"},
    "humari_radha": {"name": "Humari Radha", "ott": "zee5_p1"},
    "greatest_show": {"name": "The Greatest Show on Earth", "ott": "zee5_p1"},
    "jagadhatri": {"name": "Jagadhatri", "ott": "zee5_p1"},
    "jaane_anjaane": {"name": "Jaane Anjaane Hum Mile", "ott": "zee5_p1"},
    "pati_anaadi": {"name": "PATI ANAADI", "ott": "dangal_p1"},
    "pati_bhramachari": {"name": "PATI BHRAMACHARI", "ott": "dangal_p1"},
    "mann_atisundar": {"name": "MANN ATISUNDAR", "ott": "dangal_p1"},
    "rimjhim": {"name": "RIMJHIM", "ott": "dangal_p1"},
    "ishq_junooni": {"name": "ISHQ JUNOONI", "ott": "dangal_p1"},
    "tees_ke_paar": {"name": "TEES KE PAAR JAB MILA PYAR", "ott": "dangal_p1"},
    "kaisi_teri": {"name": "KAISI TERI DILLAGI", "ott": "dangal_p1"},
    "mann_sundar": {"name": "MANN SUNDAR", "ott": "dangal_p1"},
    "hui_gumm": {"name": "Hui Gumm Yaadein Ek Doctor Do Zindagiyaan", "ott": "sonyliv_p1"},
    "tmkoc": {"name": "Taarak Mehta Ka Ooltah Chashmah", "ott": "sonyliv_p1"},
    "hastinapur": {"name": "Hastinapur Ke Veer", "ott": "sonyliv_p1"},
    "tum_ho_naa": {"name": "Tum Ho Naa - Ghar Ki Superstar", "ott": "sonyliv_p1"},
    "pushpa": {"name": "Pushpa Impossible", "ott": "sonyliv_p1"},
    "indian_idol": {"name": "Indian Idol", "ott": "sonyliv_p1"},
    "ibd": {"name": "India's Best Dancer", "ott": "sonyliv_p1"},
    "kkk": {"name": "Khatron Ke Khiladi", "ott": "sonyliv_p1"},
    "thodi_si_umeed": {"name": "Thodi Si Umeed Thoda Sa Aasman", "ott": "sunnxt_p1"},
    "divya_prem": {"name": "Divya Prem", "ott": "sunnxt_p1"}
}

def get_all_shows():
    shows = DEFAULT_SHOWS.copy()
    for c in shows_col.find():
        shows[c["key"]] = {"name": c["name"], "ott": c["ott"]}
    return shows

def get_all_otts():
    otts = DEFAULT_OTTS.copy()
    for c in ott_col.find():
        otts.append((c["name"], c["tag"]))
    return otts

def find_db_doc_by_date(date_str):
    if not date_str:
        return None
    clean_date = date_str.strip().lower()
    alt_date = re.sub(r"^0(\d)", r"\1", clean_date) if re.match(r"^0\d", clean_date) else re.sub(r"^(\d\s)", r"0\1", clean_date)
    return video_col.find_one({
        "$or": [
            {"date": clean_date},
            {"date": alt_date},
            {"date": {"$regex": f"^{clean_date}$", "$options": "i"}},
            {"date": {"$regex": f"^{alt_date}$", "$options": "i"}}
        ]
    })

def extract_ep_and_quality(text):
    ep_match = re.search(r"(?:ep|episode|e)[._\s-]*(\d+)", text, re.IGNORECASE)
    q_match = re.search(r"(\d{3,4}p)", text, re.IGNORECASE)
    return (ep_match.group(1) if ep_match else "0"), (q_match.group(1).lower() if q_match else "default")

def extract_date_from_text(text):
    if not text:
        return None
    months_pattern = r"(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)"
    match = re.search(rf"(\d{{1,2}}\s+{months_pattern}(?:\s+\d{{4}})?|\d{{1,2}}[-/.]{months_pattern}[-/.]\d{{2,4}})", text, re.IGNORECASE)
    if match:
        raw_d = match.group(1)
        if not re.search(r"\d{4}", raw_d):
            raw_d += f" {datetime.now().year}"
        return raw_d.lower().strip()
    return None

def extract_base_title(raw_name):
    clean = re.sub(r"[-_.\s]*(TvShowHub|ANTONi|webdlbot|DG_Contents|DG_Content|UtsavTV|Nx-DRM-DL|DS_Ottwebdlbot|kairax007|ottwebdlbot|DKLR_DR|DKLRDR|DKLRShowhub)\b", "", raw_name, flags=re.IGNORECASE)
    match = re.split(r"[._\s-]+(?:Season|Episode|Ep|E\d+|\d{3,4}p|Web|Dl|AAC)", clean, flags=re.IGNORECASE)
    title_part = match[0] if match else clean
    title_part = re.sub(r"\s+", " ", title_part.replace(".", " ").replace("-", " ").replace("_", " ")).strip()
    return title_part.title() if title_part else "Unmatched Show"

def match_show(caption):
    clean_caption = caption.replace("_", " ").replace(".", " ").lower()
    for s_key, s_data in get_all_shows().items():
        if s_data["name"].lower() in clean_caption:
            return s_key
    return None

def build_html_caption(raw_name):
    clean_name = raw_name.replace("*", "").replace("<", "&lt;").replace(">", "&gt;").strip()
    base_name = re.sub(r"\.(mp4|mkv|avi|mov|webm|flv)$", "", clean_name, flags=re.IGNORECASE)
    base_name = re.sub(r"[-_.\s]+(TvShowHub|ANTONi|webdlbot|DG_Contents|DG_Content|UtsavTV|Nx-DRM-DL|DS_Ottwebdlbot|kairax007|ottwebdlbot|DKLR_DR|DKLRDR|DKLRShowhub)[-_.\s]*$", "", base_name, flags=re.IGNORECASE)
    base_name = re.sub(r"[-_]+[a-zA-Z0-9]+$", "", base_name)
    final_filename = f"{base_name.strip('.-_')}.DKLRShowhub.mp4"
    return (
        f"📄 <b>{final_filename}</b>\n\n"
        f"⚡️ <b>Join :-</b> [ <b>@DKLRShowhub</b> ]\n\n"
        f"📌 <b>Join:</b> <a href=\"https://t.me/+AT1UIPpK3c04MTk1\">https://t.me/+AT1UIPpK3c04MTk1</a>\n\n"
        f"📌 <b>Upcoming New Episode -</b> <a href=\"https://t.me/+sN83w5txQO9hNTdl\">https://t.me/+sN83w5txQO9hNTdl</a>"
    )

def remove_watermark_ffmpeg(input_path, output_path):
    cmd = [
        "ffmpeg", "-i", input_path,
        "-vf", "delogo=x=30:y=H-160:w=320:h=120",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
        "-c:a", "copy", output_path, "-y"
    ]
    subprocess.run(cmd, check=True)

def auto_save_file_to_db(clean_file_id, raw_name, target_date):
    matched_key = match_show(raw_name)
    target_date = target_date.lower().strip()
    doc = find_db_doc_by_date(target_date)
    existing_shows = doc.get("shows", {}) if doc else {}
    vid_obj = {"id": clean_file_id, "raw_name": raw_name}

    if matched_key:
        if matched_key not in existing_shows:
            existing_shows[matched_key] = []
        new_ep, new_q = extract_ep_and_quality(raw_name)
        is_replaced = False
        for idx, old_vid in enumerate(existing_shows[matched_key]):
            old_ep, old_q = extract_ep_and_quality(old_vid["raw_name"])
            if old_ep == new_ep and old_q == new_q:
                existing_shows[matched_key][idx] = vid_obj
                is_replaced = True
                break
        if not is_replaced:
            existing_shows[matched_key].append(vid_obj)
        if not doc:
            video_col.insert_one({"date": target_date, "shows": existing_shows})
        else:
            video_col.update_one({"_id": doc["_id"]}, {"$set": {"date": target_date, "shows": existing_shows}})
        return matched_key, True
    return None, False

def get_main_menu_keyboard():
    settings = get_bot_settings()
    rec_status = "🟢 Auto Receive: ON" if settings.get("auto_receive", True) else "🔴 Auto Receive: OFF"
    send_status = "🟢 Auto Send: ON" if settings.get("auto_send", True) else "🔴 Auto Send: OFF"
    src_name = settings.get("source_channel_name", "Not Set")
    tgt_name = settings.get("target_channel_name", "Not Set")

    buttons = [
        [InlineKeyboardButton("➕ Add New Show", callback_data="btn_add_show"), InlineKeyboardButton("➕ Add New OTT", callback_data="btn_add_ott")],
        [InlineKeyboardButton(rec_status, callback_data="toggle_auto_receive"), InlineKeyboardButton(send_status, callback_data="toggle_auto_send")],
        [InlineKeyboardButton(f"📥 Source: {src_name}", callback_data="btn_set_receive_channel")],
        [InlineKeyboardButton(f"📤 Target: {tgt_name}", callback_data="btn_set_send_channel")],
        [InlineKeyboardButton("⚡️ Start Batch From Forwarded Msg", callback_data="btn_start_batch")]
    ]
    return InlineKeyboardMarkup(buttons)

# ----------------- TELEGRAM BOT HANDLERS -----------------
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        update_bot_setting("admin_chat_id", update.effective_chat.id)
        await update.message.reply_text(
            "<b>नमस्ते भाई! DKLR Show Hub Engine Live!</b>\n\n"
            "👉 सोर्स चैनल की सभी वीडियोज वॉटरमार्क हटकर, आपका कस्टम टाइटल लगकर सीधे टारगेट चैनल पर जाएँगी।\n"
            "👉 तारीख मिलने पर डेटाबेस में अपने आप ऐड होगी, न मिलने पर बॉट आपसे तारीख माँगेगा।\n\n"
            "👇 <b>कंट्रोल पैनल:</b>",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML"
        )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    msg = update.message
    text = (msg.text or "").strip()

    if context.user_data.get("awaiting_missing_date"):
        target_date = text.lower().strip()
        context.user_data["awaiting_missing_date"] = False
        missing_list = context.user_data.get("missing_date_vids", [])
        context.user_data["missing_date_vids"] = []
        for item in missing_list:
            auto_save_file_to_db(item["id"], item["raw_name"], target_date)
        await msg.reply_text(f"✅ <b>तारीख सेट हो गई:</b> <b>{target_date.title()}</b>\n📁 कुल <b>{len(missing_list)} वीडियोस</b> डेटाबेस में सेव कर दी गई हैं!", parse_mode="HTML")
        return

    if context.user_data.get("setting_receive_channel"):
        ch_id = msg.forward_from_chat.id if msg.forward_from_chat else text.replace("https://t.me/", "").replace("@", "").strip()
        ch_title = msg.forward_from_chat.title if msg.forward_from_chat else str(ch_id)
        if ch_id:
            update_bot_setting("source_channel_id", ch_id)
            update_bot_setting("source_channel_name", ch_title)
            context.user_data["setting_receive_channel"] = False
            await msg.reply_text(f"🎯 <b>Source Channel सेट हो गया:</b> <code>{ch_title}</code>\n🆔 <b>Channel ID:</b> <code>{ch_id}</code>", reply_markup=get_main_menu_keyboard(), parse_mode="HTML")
            return

    if context.user_data.get("setting_send_channel"):
        target_id = msg.forward_from_chat.id if msg.forward_from_chat else ("@" + text.replace("https://t.me/", "").replace("@", "").strip())
        target_title = msg.forward_from_chat.title if msg.forward_from_chat else str(target_id)
        if target_id:
            update_bot_setting("target_channel_id", target_id)
            update_bot_setting("target_channel_name", target_title)
            context.user_data["setting_send_channel"] = False
            await msg.reply_text(f"🎯 <b>Target Channel सेट हो गया:</b> <code>{target_title}</code>\n🆔 <b>Target ID:</b> <code>{target_id}</code>", reply_markup=get_main_menu_keyboard(), parse_mode="HTML")
            return

    # Date Search
    months = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]
    if any(m in text.lower() for m in months) and re.search(r'\d+', text):
        user_input_date = text.lower().strip()
        context.user_data["active_date"] = user_input_date
        all_shows = get_all_shows()
        doc = find_db_doc_by_date(user_input_date)
        uploaded_shows_dict = doc.get("shows", {}) if doc else {}
        uploaded_ott_tags = {all_shows[s_key]["ott"] for s_key in uploaded_shows_dict if s_key in all_shows and len(uploaded_shows_dict[s_key]) > 0}

        buttons = [[InlineKeyboardButton(o_name, callback_data=f"o|{o_tag}")] for o_name, o_tag in get_all_otts() if o_tag in uploaded_ott_tags]
        if buttons:
            buttons.append([InlineKeyboardButton("❌ Close", callback_data="close")])
            await msg.reply_text(f"✅ <b>Data fetched successfully!</b>\n\n📅 <b>Date Requested:</b>\n<b>{text.title()}</b>\n\n🔍 <b>Please choose your desired OTT below:</b>", reply_markup=InlineKeyboardMarkup(buttons), parse_mode="HTML")
        else:
            await msg.reply_text(f"❌ <b>इस तारीख ({text.title()}) में कोई भी वीडियो उपलब्ध नहीं है!</b>", parse_mode="HTML")

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "close":
        await query.message.delete()
    elif data == "toggle_auto_receive":
        settings = get_bot_settings()
        update_bot_setting("auto_receive", not settings.get("auto_receive", True))
        await query.message.edit_reply_markup(reply_markup=get_main_menu_keyboard())
    elif data == "toggle_auto_send":
        settings = get_bot_settings()
        update_bot_setting("auto_send", not settings.get("auto_send", True))
        await query.message.edit_reply_markup(reply_markup=get_main_menu_keyboard())
    elif data == "btn_set_receive_channel":
        context.user_data["setting_receive_channel"] = True
        await query.message.reply_text("📥 <b>सोर्स चैनल से कोई भी एक मैसेज Forward करें:</b>", parse_mode="HTML")
    elif data == "btn_set_send_channel":
        context.user_data["setting_send_channel"] = True
        await query.message.reply_text("📤 <b>टारगेट चैनल से कोई भी एक मैसेज Forward करें:</b>", parse_mode="HTML")

# ----------------- MAIN RUNNER -----------------
async def main_async():
    global tg_bot_app, pyrogram_userbot

    tg_bot_app = ApplicationBuilder().token(BOT_TOKEN).build()
    tg_bot_app.add_handler(CommandHandler("start", start_command))
    tg_bot_app.add_handler(MessageHandler((tg_filters.TEXT | tg_filters.FORWARDED) & ~tg_filters.COMMAND, handle_text))
    tg_bot_app.add_handler(CallbackQueryHandler(button_click))

    await tg_bot_app.initialize()
    await tg_bot_app.start()
    await tg_bot_app.updater.start_polling()
    print("✅ [Telegram Bot] Polling Active!")

    if SESSION_STRING:
        try:
            pyrogram_userbot = Client("dklr_userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
            await pyrogram_userbot.start()
            print("✅ [UserBot] Pyrogram Engine Active!")
        except Exception as e:
            print(f"⚠️ UserBot Start Error: {e}")
    else:
        print("⚠️ [SESSION_STRING] not set. Running Telegram Bot only.")

    # Keep Async Loop Alive Forever
    while True:
        await asyncio.sleep(3600)

def main():
    try:
        asyncio.run(main_async())
    except (KeyboardInterrupt, SystemExit):
        pass

if __name__ == "__main__":
    main()

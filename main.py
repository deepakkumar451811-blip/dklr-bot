import os
import re
import asyncio
import subprocess
from threading import Thread
from datetime import datetime
from flask import Flask
import pymongo
from bson.objectid import ObjectId
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

# ----------------- FLASK SERVER -----------------
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "DKLR Show Hub V2 Active!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

keep_alive()

# ----------------- CONFIG & HARDCODED CREDENTIALS -----------------
BOT_TOKEN = "8658926437:AAHnzF23ypbzIbZ-yATBhA0MHFGVOhVsTzA"
MONGO_URI = "mongodb+srv://deepakkumar451811_db_user:z0gBb13CSvYAECgG@cluster0.osysn1c.mongodb.net/?appName=Cluster0"
API_ID = 30366893
API_HASH = "ecb01a29588b13c36c8c373584270ea8"

SESSION_STRING = "1BVtsOIsBuy0WziD0rLnUDscaySskfhveyGx4zv0hYUqWI0RNfdIHU6eEyXFuTcszbb1xpwuec0H5-z2yAx2t2LQe6HDFqloLolKf2L5czt39pECanLIPjv2Le9tCEck2W991g_0bDk96jYZm7ZUVvQNRUo0Ka3XzMRPZyHynuwFlyTcvkYeZuREx9sDjo1vRFtA-NgX7Z5k9Mz-rg0ZVSmmXY1FbYj8ru-Gnmd_z-RxbbBfydbFFS_SVPkcJXJIkIC0HbG9QShsLGRIZazHyK25ATxnEcYjZYNW17PrLW6Ux0-2Yvx0q0WAvWKPIfGeIDwevfJuy8mvK0Wd6DpDmZEYzVJ26eUI="
OWNER_USERNAME = "dklr145"

client = pymongo.MongoClient(MONGO_URI)
db = client["dklr_bot_db"]
video_col = db["videos"]
shows_col = db["custom_shows"]
ott_col = db["custom_otts"]
settings_col = db["bot_settings"]
audio_series_col = db["audio_series"]

userbot = Client(
    "dklr_userbot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING,
    in_memory=True
)

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

# ----------------- BATCH ENGINE -----------------
async def process_batch_from_id(chat_id, start_msg_id, target_id, reply_chat_id, context):
    if not userbot.is_connected:
        try:
            await userbot.start()
        except Exception as e:
            await context.bot.send_message(chat_id=reply_chat_id, text=f"❌ <b>UserBot Connect Error:</b> <code>{e}</code>", parse_mode="HTML")
            return

    await context.bot.send_message(
        chat_id=reply_chat_id,
        text=f"🚀 <b>Batch Processing शुरू हो गई है!</b>\n👉 मैसेज ID <code>{start_msg_id}</code> से वीडियो प्रोसेस हो रही हैं...",
        parse_mode="HTML"
    )

    processed_count = 0
    try:
        messages_to_process = []
        async for message in userbot.get_chat_history(chat_id):
            if message.id < start_msg_id:
                break
            if message.video or message.document:
                messages_to_process.append(message)

        messages_to_process.reverse()

        for message in messages_to_process:
            input_file = None
            output_file = None
            raw_name = message.caption or (message.video and message.video.file_name) or (message.document and message.document.file_name) or "Episode_Video.mp4"
            msg_date = extract_date_from_text(raw_name)
            needs_cleaning = has_watermark(raw_name)

            try:
                custom_caption = build_html_caption(raw_name)
                clean_file_id = None

                if needs_cleaning:
                    input_file = await message.download()
                    output_file = f"clean_{os.path.basename(input_file)}"
                    loop = asyncio.get_running_loop()
                    await loop.run_in_executor(None, remove_watermark_ffmpeg, input_file, output_file)
                    sent_msg = await userbot.send_document(chat_id=target_id, document=output_file, caption=custom_caption)
                    clean_file_id = sent_msg.document.file_id if sent_msg.document else sent_msg.video.file_id
                else:
                    sent_msg = await message.copy(chat_id=target_id, caption=custom_caption)
                    clean_file_id = sent_msg.document.file_id if sent_msg.document else sent_msg.video.file_id

                processed_count += 1

                if msg_date:
                    matched_key, is_saved = auto_save_file_to_db(clean_file_id, raw_name, msg_date)
                    if not is_saved:
                        base_t = extract_base_title(raw_name)
                        btn = InlineKeyboardMarkup([[InlineKeyboardButton(f"➕ Add '{base_t}'", callback_data="btn_add_show")]])
                        await context.bot.send_message(chat_id=reply_chat_id, text=f"🚨 <b>Unmatched Show!</b>\n🎬 <b>Title:</b> {base_t}\n📅 <b>Date:</b> {msg_date.title()}\n👇 शो जोड़ने के लिए नीचे दबाएँ:", reply_markup=btn, parse_mode="HTML")
                else:
                    if "missing_date_vids" not in context.user_data:
                        context.user_data["missing_date_vids"] = []
                    context.user_data["missing_date_vids"].append({"id": clean_file_id, "raw_name": raw_name})
                    context.user_data["awaiting_missing_date"] = True
                    await context.bot.send_message(chat_id=reply_chat_id, text=f"⚠️ <b>तारीख नहीं मिली!</b>\n🎬 <b>File:</b> {raw_name}\n\n✍️ <b>कृपया तारीख लिखकर भेजें (उदा: 16 August 2026):</b>", parse_mode="HTML")

            except Exception as e:
                print(f"⚠️ [Batch File Error]: {e}")
            finally:
                if input_file and os.path.exists(input_file):
                    os.remove(input_file)
                if output_file and os.path.exists(output_file):
                    os.remove(output_file)

        await context.bot.send_message(chat_id=reply_chat_id, text=f"🎉 <b>Batch Complete!</b>\n✅ कुल <b>{processed_count} वीडियोस</b> टारगेट चैनल पर भेज दी गई हैं।", parse_mode="HTML")
    except Exception as e:
        print(f"❌ [Batch Error]: {e}")

# ----------------- KEYBOARDS -----------------
def get_home_keyboard():
    buttons = [
        [InlineKeyboardButton("📺 Daily TV Shows (Date Wise)", callback_data="nav_how_to_watch")],
        [
            InlineKeyboardButton("🎧 Pocket FM Stories", callback_data="audio_plat|pocketfm"),
            InlineKeyboardButton("📻 Kuku FM Stories", callback_data="audio_plat|kukufm")
        ],
        [InlineKeyboardButton("⚙️ Admin Control Panel", callback_data="nav_admin_panel")]
    ]
    return InlineKeyboardMarkup(buttons)

def get_admin_menu_keyboard():
    settings = get_bot_settings()
    rec_status = "🟢 Auto Receive: ON" if settings.get("auto_receive", True) else "🔴 Auto Receive: OFF"
    send_status = "🟢 Auto Send: ON" if settings.get("auto_send", True) else "🔴 Auto Send: OFF"
    src_name = settings.get("source_channel_name", "Not Set")
    tgt_name = settings.get("target_channel_name", "Not Set")

    buttons = [
        [InlineKeyboardButton("➕ Add New TV Show", callback_data="btn_add_show"), InlineKeyboardButton("➕ Add New OTT", callback_data="btn_add_ott")],
        [InlineKeyboardButton("➕ Add Pocket FM Story", callback_data="btn_add_audio_story|pocketfm"), InlineKeyboardButton("➕ Add Kuku FM Story", callback_data="btn_add_audio_story|kukufm")],
        [InlineKeyboardButton(rec_status, callback_data="toggle_auto_receive"), InlineKeyboardButton(send_status, callback_data="toggle_auto_send")],
        [InlineKeyboardButton(f"📥 Source: {src_name}", callback_data="btn_set_receive_channel")],
        [InlineKeyboardButton(f"📤 Target: {tgt_name}", callback_data="btn_set_send_channel")],
        [InlineKeyboardButton("⚡️ Start Batch Cleaner", callback_data="btn_start_batch")],
        [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="nav_home")]
    ]
    return InlineKeyboardMarkup(buttons)

# ----------------- TELEGRAM BOT HANDLERS -----------------
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        update_bot_setting("admin_chat_id", update.effective_chat.id)
        welcome_text = (
            "✨ <b>DKLR Show Hub & Audio Series Bot में आपका स्वागत है!</b> ✨\n\n"
            "👇 <b>आप नीचे दिए गए विकल्पों में से चुन सकते हैं:</b>\n"
            "▫️ <b>Daily TV Shows:</b> तारीख लिखकर भेजें और अपने पसंदीदा शो देखें।\n"
            "▫️ <b>Pocket FM & Kuku FM:</b> ऑडियो स्टोरीज़ और उनके एपिसोड सुनें।"
        )
        await update.message.reply_text(welcome_text, reply_markup=get_home_keyboard(), parse_mode="HTML")

async def handle_media_or_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    msg = update.message
    text = (msg.text or "").strip()

    # 1. ADDING NEW PACK NAME (e.g. Episode 01 To 100)
    if context.user_data.get("adding_pack_name"):
        pack_name = text
        story_id = context.user_data.get("active_story_id")
        context.user_data["adding_pack_name"] = False

        audio_series_col.update_one(
            {"_id": ObjectId(story_id)},
            {"$push": {"packs": {"name": pack_name, "files": []}}}
        )
        await msg.reply_text(
            f"✅ <b>नया पैक बना दिया गया:</b> <b>{pack_name}</b>\n\n"
            f"👉 नीचे दिए बटन पर क्लिक करके इसमें ऑडियो या फाइलें अपलोड करें:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📖 Open Story", callback_data=f"open_story|{story_id}")]]),
            parse_mode="HTML"
        )
        return

    # 2. UPLOADING AUDIO/ZIP FILE TO PACK
    if context.user_data.get("awaiting_pack_file"):
        target_obj = msg.audio or msg.voice or msg.document or msg.video
        if target_obj:
            file_id = target_obj.file_id
            story_id = context.user_data.get("active_story_id")
            pack_idx = context.user_data.get("active_pack_idx")
            file_name = msg.caption or getattr(target_obj, 'file_name', None) or f"Audio File ({datetime.now().strftime('%d %b')})"

            doc = audio_series_col.find_one({"_id": ObjectId(story_id)})
            if doc and "packs" in doc and len(doc["packs"]) > pack_idx:
                doc["packs"][pack_idx]["files"].append({"file_id": file_id, "name": file_name})
                audio_series_col.update_one({"_id": ObjectId(story_id)}, {"$set": {"packs": doc["packs"]}})

            context.user_data["awaiting_pack_file"] = False
            await msg.reply_text(
                f"✅ <b>फ़ाइल पैक में अपलोड हो गई!</b>\n📁 <b>Name:</b> {file_name}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back to Pack", callback_data=f"open_pack|{story_id}|{pack_idx}")]),
                parse_mode="HTML"
            )
            return
        else:
            await msg.reply_text("⚠️ <b>कृपया ऑडियो, Zip, Document या वीडियो फ़ाइल भेजें!</b>", parse_mode="HTML")
            return

    # 3. ADDING AUDIO STORY NAME
    if context.user_data.get("adding_audio_story_name"):
        story_name = text.title()
        plat = context.user_data.get("audio_target_plat")
        context.user_data["adding_audio_story_name"] = False
        
        inserted = audio_series_col.insert_one({
            "platform": plat,
            "title": story_name,
            "packs": []
        })
        story_id = str(inserted.inserted_id)

        await msg.reply_text(
            f"✅ <b>नई स्टोरी जोड़ी गई:</b> <b>{story_name}</b> ({plat.upper()})\n\n"
            f"👇 <b>अब इसमें Episode Pack जोड़ने के लिए नीचे दबाएँ:</b>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Add Episode Pack (e.g. 01 To 100)", callback_data=f"btn_create_pack|{story_id}")],
                [InlineKeyboardButton("📖 Open Story", callback_data=f"open_story|{story_id}")]
            ]),
            parse_mode="HTML"
        )
        return

    # 4. MISSING DATE HANDLER
    if context.user_data.get("awaiting_missing_date"):
        target_date = text.lower().strip()
        context.user_data["awaiting_missing_date"] = False
        missing_list = context.user_data.get("missing_date_vids", [])
        context.user_data["missing_date_vids"] = []
        for item in missing_list:
            auto_save_file_to_db(item["id"], item["raw_name"], target_date)
        await msg.reply_text(f"✅ <b>तारीख सेट हो गई:</b> <b>{target_date.title()}</b>\n📁 कुल <b>{len(missing_list)} वीडियोस</b> डेटाबेस में सेव कर दी गई हैं!", parse_mode="HTML")
        return

    # 5. BATCH FORWARD RECEIVER
    if context.user_data.get("awaiting_batch_forward"):
        if msg.forward_from_chat and msg.forward_from_message_id:
            source_chat_id = msg.forward_from_chat.id
            start_id = msg.forward_from_message_id
            settings = get_bot_settings()
            target_id = settings.get("target_channel_id")
            if not target_id:
                await msg.reply_text("❌ <b>कृपया पहले 'Target Channel' सेट करें!</b>", parse_mode="HTML")
                return
            context.user_data["awaiting_batch_forward"] = False
            asyncio.create_task(process_batch_from_id(source_chat_id, start_id, target_id, update.effective_chat.id, context))
            return
        else:
            await msg.reply_text("⚠️ <b>कृपया सोर्स चैनल से ही कोई SMS या Video फॉरवर्ड करें!</b>", parse_mode="HTML")
            return

    # 6. SET SOURCE CHANNEL
    if context.user_data.get("setting_receive_channel"):
        ch_id = msg.forward_from_chat.id if msg.forward_from_chat else text.replace("https://t.me/", "").replace("@", "").strip()
        ch_title = msg.forward_from_chat.title if msg.forward_from_chat else str(ch_id)
        if ch_id:
            update_bot_setting("source_channel_id", ch_id)
            update_bot_setting("source_channel_name", ch_title)
            context.user_data["setting_receive_channel"] = False
            await msg.reply_text(f"🎯 <b>Source Channel सेट हो गया:</b> <code>{ch_title}</code>\n🆔 <b>Channel ID:</b> <code>{ch_id}</code>", reply_markup=get_admin_menu_keyboard(), parse_mode="HTML")
            return

    # 7. SET TARGET CHANNEL
    if context.user_data.get("setting_send_channel"):
        target_id = msg.forward_from_chat.id if msg.forward_from_chat else ("@" + text.replace("https://t.me/", "").replace("@", "").strip())
        target_title = msg.forward_from_chat.title if msg.forward_from_chat else str(target_id)
        if target_id:
            update_bot_setting("target_channel_id", target_id)
            update_bot_setting("target_channel_name", target_title)
            context.user_data["setting_send_channel"] = False
            await msg.reply_text(f"🎯 <b>Target Channel सेट हो गया:</b> <code>{target_title}</code>\n🆔 <b>Target ID:</b> <code>{target_id}</code>", reply_markup=get_admin_menu_keyboard(), parse_mode="HTML")
            return

    # 8. ADD NEW TV SHOW
    if context.user_data.get("adding_new_show_step1"):
        show_name = text.strip().title()
        context.user_data["temp_show_name"] = show_name
        context.user_data["temp_show_key"] = show_name.lower().replace(" ", "_")
        context.user_data["adding_new_show_step1"] = False
        ott_buttons = [[InlineKeyboardButton(o_name, callback_data=f"save_show_ott|{o_tag}")] for o_name, o_tag in get_all_otts()]
        await msg.reply_text(f"🎬 <b>Show Name:</b> {show_name}\n\n👇 <b>OTT चुनें:</b>", reply_markup=InlineKeyboardMarkup(ott_buttons), parse_mode="HTML")
        return

    # 9. ADD NEW OTT
    if context.user_data.get("adding_new_ott_mode"):
        ott_name = text.strip()
        ott_tag = ott_name.lower().replace(" ", "") + "_p1"
        ott_col.update_one({"tag": ott_tag}, {"$set": {"name": ott_name, "tag": ott_tag}}, upsert=True)
        context.user_data["adding_new_ott_mode"] = False
        await msg.reply_text(f"✅ <b>नया OTT जोड़ा गया:</b> {ott_name}", reply_markup=get_admin_menu_keyboard(), parse_mode="HTML")
        return

    # 10. DATE SEARCH (TV SHOWS)
    months = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december", "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
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
    elif data == "nav_home":
        await query.message.edit_text("✨ <b>DKLR Show Hub Main Menu:</b>", reply_markup=get_home_keyboard(), parse_mode="HTML")
    elif data == "nav_how_to_watch":
        await query.message.edit_text(
            "📺 <b>Daily TV Shows कैसे देखें?</b>\n\n"
            "👉 चैट में जिस तारीख का एपिसोड देखना है, वह तारीख लिखकर भेजें।\n"
            "📝 <b>उदाहरण:</b> <code>16 August 2026</code> या <code>14 Aug</code>\n\n"
            "बॉट तुरंत उस तारीख के सभी OTT और सीरियल आपके सामने ला देगा!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="nav_home")]]),
            parse_mode="HTML"
        )
    elif data == "nav_admin_panel":
        await query.message.edit_text("⚙️ <b>Admin Control Panel:</b>", reply_markup=get_admin_menu_keyboard(), parse_mode="HTML")

    # 1. Audio Platform Stories List
    elif data.startswith("audio_plat|"):
        plat = data.split("|")[1]
        plat_title = "Pocket FM" if plat == "pocketfm" else "Kuku FM"
        stories = list(audio_series_col.find({"platform": plat}))
        
        buttons = []
        for s in stories:
            total_packs = len(s.get("packs", []))
            buttons.append([InlineKeyboardButton(f"🎧 {s['title']} ({total_packs} Packs)", callback_data=f"open_story|{str(s['_id'])}")])
        
        buttons.append([InlineKeyboardButton("➕ Add New Story", callback_data=f"btn_add_audio_story|{plat}")])
        buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="nav_home")])
        
        await query.message.edit_text(
            f"🎙 <b>{plat_title} Stories:</b>\n👇 अपनी पसंदीदा स्टोरी चुनें या नई स्टोरी जोड़ें:",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="HTML"
        )

    # 2. Open Story -> Shows Packs / Direct Episodes & Delete Option
    elif data.startswith("open_story|"):
        story_id = data.split("|")[1]
        story = audio_series_col.find_one({"_id": ObjectId(story_id)})
        if not story:
            await query.message.reply_text("❌ स्टोरी नहीं मिली!")
            return

        # Auto-convert old structure to new packs if needed
        if "episodes" in story and len(story["episodes"]) > 0 and ("packs" not in story or len(story["packs"]) == 0):
            old_eps = story["episodes"]
            audio_series_col.update_one(
                {"_id": ObjectId(story_id)},
                {"$set": {"packs": [{"name": "Episode 01 To 100", "files": [{"file_id": e["file_id"], "name": e["title"]} for e in old_eps]}], "episodes": []}}
            )
            story = audio_series_col.find_one({"_id": ObjectId(story_id)})

        buttons = []
        for idx, pack in enumerate(story.get("packs", [])):
            file_count = len(pack.get("files", []))
            buttons.append([InlineKeyboardButton(f"📁 {pack['name']} ({file_count} Files)", callback_data=f"open_pack|{story_id}|{idx}")])

        buttons.append([InlineKeyboardButton("➕ Add Episode Pack (e.g. 01 To 100)", callback_data=f"btn_create_pack|{story_id}")])
        buttons.append([InlineKeyboardButton("🗑 Delete this Story", callback_data=f"del_story|{story_id}")])
        buttons.append([InlineKeyboardButton("⬅️ Back", callback_data=f"audio_plat|{story['platform']}")])

        await query.message.edit_text(
            f"📖 <b>Story:</b> <b>{story['title']}</b>\n📻 <b>Platform:</b> {story['platform'].upper()}\n\n"
            f"👇 <b>एपिसोड पैक चुनें या नया पैक जोड़ें:</b>",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="HTML"
        )

    # Delete Story Handler
    elif data.startswith("del_story|"):
        story_id = data.split("|")[1]
        story = audio_series_col.find_one({"_id": ObjectId(story_id)})
        plat = story["platform"] if story else "pocketfm"
        audio_series_col.delete_one({"_id": ObjectId(story_id)})
        await query.message.edit_text(f"🗑 <b>स्टोरी डेटाबेस से हटा दी गई है!</b>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back to Stories", callback_data=f"audio_plat|{plat}")]]), parse_mode="HTML")

    # 3. Create New Pack Prompt
    elif data.startswith("btn_create_pack|"):
        story_id = data.split("|")[1]
        context.user_data["adding_pack_name"] = True
        context.user_data["active_story_id"] = story_id
        await query.message.reply_text(
            "✍️ <b>कृपया एपिसोड पैक का नाम लिखकर भेजें:</b>\n\n"
            "📝 <b>उदाहरण:</b> <code>Episode 01 To 100</code> या <code>Episode 101 To 200</code>",
            parse_mode="HTML"
        )

    # 4. Open Pack -> Shows Files & Upload Button
    elif data.startswith("open_pack|"):
        _, story_id, pack_idx_str = data.split("|")
        pack_idx = int(pack_idx_str)
        story = audio_series_col.find_one({"_id": ObjectId(story_id)})
        pack = story["packs"][pack_idx]

        buttons = []
        for f_idx, f_item in enumerate(pack.get("files", [])):
            buttons.append([InlineKeyboardButton(f"▶️ Play: {f_item['name'][:25]}", callback_data=f"play_pack_file|{story_id}|{pack_idx}|{f_idx}")])

        buttons.append([InlineKeyboardButton("📤 Upload File to this Pack", callback_data=f"btn_upload_to_pack|{story_id}|{pack_idx}")])
        buttons.append([InlineKeyboardButton("⬅️ Back to Packs", callback_data=f"open_story|{story_id}")])

        await query.message.edit_text(
            f"📖 <b>Story:</b> {story['title']}\n"
            f"📁 <b>Pack:</b> <b>{pack['name']}</b>\n\n"
            f"👇 <b>सुनने के लिए क्लिक करें या नई फ़ाइल अपलोड करें:</b>",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="HTML"
        )

    # 5. Upload File to Pack Prompt
    elif data.startswith("btn_upload_to_pack|"):
        _, story_id, pack_idx_str = data.split("|")
        context.user_data["active_story_id"] = story_id
        context.user_data["active_pack_idx"] = int(pack_idx_str)
        context.user_data["awaiting_pack_file"] = True
        await query.message.reply_text("🎙 <b>कृपया इस पैक के लिए ऑडियो, Zip, Document या वीडियो फ़ाइल यहाँ भेजें:</b>", parse_mode="HTML")

    # 6. Play File from Pack with 2 Hours Auto-Delete
    elif data.startswith("play_pack_file|"):
        _, story_id, pack_idx_str, f_idx_str = data.split("|")
        story = audio_series_col.find_one({"_id": ObjectId(story_id)})
        pack = story["packs"][int(pack_idx_str)]
        f_item = pack["files"][int(f_idx_str)]

        sent_msg = await context.bot.send_document(
            chat_id=query.message.chat_id,
            document=f_item["file_id"],
            caption=f"🎧 <b>{story['title']}</b> - <b>{pack['name']}</b>\n📁 <b>File:</b> {f_item['name']}\n\n⚡️ <b>DKLR Show Hub</b>",
            parse_mode="HTML"
        )
        
        notice = await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="⏰ <b>यह फ़ाइल कॉपीराइट सुरक्षा के लिए 2 घंटे (120 मिनट) बाद ऑटो-डिलीट हो जाएगी। इसे 'Saved Messages' में सुरक्षित कर लें!</b>",
            parse_mode="HTML"
        )

        async def auto_delete_story_task(chat_id, msg_ids):
            await asyncio.sleep(7200)
            for mid in msg_ids:
                try:
                    await context.bot.delete_message(chat_id=chat_id, message_id=mid)
                except Exception:
                    pass

        asyncio.create_task(auto_delete_story_task(query.message.chat_id, [sent_msg.message_id, notice.message_id]))

    # Admin Add Story Name
    elif data.startswith("btn_add_audio_story|"):
        plat = data.split("|")[1]
        context.user_data["adding_audio_story_name"] = True
        context.user_data["audio_target_plat"] = plat
        await query.message.reply_text(f"✍️ <b>कृपया {plat.upper()} की नई स्टोरी का नाम लिखकर भेजें:</b>", parse_mode="HTML")

    # TV Controls
    elif data == "toggle_auto_receive":
        settings = get_bot_settings()
        update_bot_setting("auto_receive", not settings.get("auto_receive", True))
        await query.message.edit_reply_markup(reply_markup=get_admin_menu_keyboard())
    elif data == "toggle_auto_send":
        settings = get_bot_settings()
        update_bot_setting("auto_send", not settings.get("auto_send", True))
        await query.message.edit_reply_markup(reply_markup=get_admin_menu_keyboard())
    elif data == "btn_set_receive_channel":
        context.user_data["setting_receive_channel"] = True
        await query.message.reply_text("📥 <b>सोर्स चैनल से कोई भी एक मैसेज Forward करें:</b>", parse_mode="HTML")
    elif data == "btn_set_send_channel":
        context.user_data["setting_send_channel"] = True
        await query.message.reply_text("📤 <b>टारगेट चैनल से कोई भी एक मैसेज Forward करें:</b>", parse_mode="HTML")
    elif data == "btn_start_batch":
        context.user_data["awaiting_batch_forward"] = True
        await query.message.reply_text("⚡️ <b>Batch Cleaner Active!</b>\n\n👉 सोर्स चैनल से वह <b>SMS या Video Forward करें</b> जहाँ से प्रोसेस शुरू करना चाहते हैं।", parse_mode="HTML")
    elif data == "btn_add_show":
        context.user_data["adding_new_show_step1"] = True
        await query.message.reply_text("✍️ <b>कृपया नए TV शो का नाम लिखकर भेजें:</b>", parse_mode="HTML")
    elif data == "btn_add_ott":
        context.user_data["adding_new_ott_mode"] = True
        await query.message.reply_text("✍️ <b>कृपया नए OTT का नाम लिखकर भेजें:</b>", parse_mode="HTML")
    elif data.startswith("save_show_ott|"):
        ott_tag = data.split("|")[1]
        show_name = context.user_data.get("temp_show_name")
        show_key = context.user_data.get("temp_show_key")
        shows_col.update_one({"key": show_key}, {"$set": {"key": show_key, "name": show_name, "ott": ott_tag}}, upsert=True)
        await query.message.reply_text(f"✅ <b>नया TV शो जोड़ा गया:</b> {show_name}", reply_markup=get_admin_menu_keyboard(), parse_mode="HTML")

    # Date OTT Shows Flow
    user_date = context.user_data.get("active_date", "")
    if data.startswith("o|"):
        ott_tag = data.split("|")[1]
        all_shows = get_all_shows()
        doc = find_db_doc_by_date(user_date)
        uploaded_shows_dict = doc.get("shows", {}) if doc else {}

        show_buttons = []
        for key, info in all_shows.items():
            if info["ott"] == ott_tag and key in uploaded_shows_dict and len(uploaded_shows_dict[key]) > 0:
                show_buttons.append([InlineKeyboardButton(f"{info['name']} ↗️", callback_data=f"s|{key}")])

        disp_date = user_date.title() if user_date else "Selected Date"
        if show_buttons:
            show_buttons.append([InlineKeyboardButton("❌ Close", callback_data="close")])
            await query.message.edit_text(f"🎬 <b>{ott_tag.split('_')[0].upper()} Shows ({disp_date}):</b>", reply_markup=InlineKeyboardMarkup(show_buttons), parse_mode="HTML")

    elif data.startswith("s|"):
        show_key = data.split("|")[1]
        doc = find_db_doc_by_date(user_date)
        video_list = doc.get("shows", {}).get(show_key, []) if doc else []

        if video_list:
            sent_messages = []
            for vid_obj in video_list:
                r_name = vid_obj.get("raw_name", "Episode_Video.DKLRShowhub.mp4")
                fresh_caption = build_html_caption(r_name)
                sent_vid = await context.bot.send_document(chat_id=query.message.chat_id, document=vid_obj["id"], caption=fresh_caption, parse_mode="HTML")
                sent_messages.append(sent_vid.message_id)

            notice = await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="⏰ <b>वीडियोज़ 60 मिनट बाद ऑटो-डिलीट हो जाएँगी! इन्हें Saved Messages में फॉरवर्ड कर लें।</b>",
                parse_mode="HTML"
            )
            sent_messages.append(notice.message_id)

            async def auto_delete_task(chat_id, msg_ids):
                await asyncio.sleep(3600)
                for mid in msg_ids:
                    try:
                        await context.bot.delete_message(chat_id=chat_id, message_id=mid)
                    except Exception:
                        pass

            asyncio.create_task(auto_delete_task(query.message.chat_id, sent_messages))

# ----------------- MAIN RUNNER -----------------
async def main_async():
    print("🚀 Starting UserBot Engine...")
    try:
        await userbot.start()
        print("✅ [UserBot] Pyrogram Engine Connected!")
    except Exception as e:
        print(f"⚠️ UserBot Start Error: {e}")

    print("🚀 Starting Telegram Bot...")
    tg_bot_app = ApplicationBuilder().token(BOT_TOKEN).build()
    tg_bot_app.add_handler(CommandHandler("start", start_command))
    tg_bot_app.add_handler(MessageHandler((tg_filters.ALL) & ~tg_filters.COMMAND, handle_media_or_text))
    tg_bot_app.add_handler(CallbackQueryHandler(button_click))

    await tg_bot_app.initialize()
    await tg_bot_app.start()
    await tg_bot_app.updater.start_polling()
    print("✅ [Telegram Bot] Live & Listening!")

    while True:
        await asyncio.sleep(3600)

def main():
    try:
        asyncio.run(main_async())
    except (KeyboardInterrupt, SystemExit):
        pass

if __name__ == "__main__":
    main()

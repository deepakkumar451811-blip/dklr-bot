import asyncio
from datetime import datetime
import io
import os
import re
import subprocess
from threading import Thread
from flask import Flask
import pymongo
from pyrogram import Client, filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters as tg_filters,
)

# ----------------- FLASK SERVER (KEEP-ALIVE) -----------------
app_flask = Flask(__name__)


@app_flask.route("/")
def home():
  return "DKLR Show Hub Engine Active!"


def run_flask():
  port = int(os.environ.get("PORT", 8080))
  app_flask.run(host="0.0.0.0", port=port)


def keep_alive():
  t = Thread(target=run_flask)
  t.start()


keep_alive()

# ----------------- CONFIG & DB -----------------
BOT_TOKEN = os.environ.get(
    "BOT_TOKEN", "8658926437:AAHnzF23ypbzIbZ-yATBhA0MHFGVOhVsTzA"
)
MONGO_URI = os.environ.get(
    "MONGO_URI",
    "mongodb+srv://deepakkumar451811_db_user:z0gBb13CSvYAECgG@cluster0.osysn1c.mongodb.net/?appName=Cluster0",
)
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


# ----------------- SETTINGS MANAGEMENT -----------------
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
        "admin_chat_id": None,
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
    ("SonyLiv", "sonyliv_p1"),
]

DEFAULT_SHOWS = {
    # HOTSTAR
    "shivmay_shravan": {"name": "Shivmay Shravan", "ott": "hotstar_p1"},
    "binddii": {"name": "Binddii", "ott": "hotstar_p1"},
    "oh_humnava": {
        "name": "Oh Humnava - Tum Dena Saath Mera",
        "ott": "hotstar_p1",
    },
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
    "kyunki_saas": {
        "name": "Kyunki Saas Bhi Kabhi Bahu Thi",
        "ott": "hotstar_p1",
    },
    "kyunki_rishton": {
        "name": "Kyunki Rishton Ke Bhi Roop Badalte Hain",
        "ott": "hotstar_p1",
    },
    "fevicreate": {"name": "Fevicreate Idea Labs", "ott": "hotstar_p1"},
    "laughter_chefs": {
        "name": "Laughter Chefs Unlimited Entertainment",
        "ott": "hotstar_p1",
    },
    # ZEE5
    "tu_hi_re": {"name": "Tu Hi Re Dil Mein", "ott": "zee5_p1"},
    "lakshmi_nivas": {"name": "Lakshmi Nivas", "ott": "zee5_p1"},
    "tumm_se_tumm": {"name": "Tumm Se Tumm Tak", "ott": "zee5_p1"},
    "ganga_mai": {"name": "Ganga Mai Ki Betiyan", "ott": "zee5_p1"},
    "vasudha": {"name": "Vasudha", "ott": "zee5_p1"},
    "humari_radha": {"name": "Humari Radha", "ott": "zee5_p1"},
    "jagadhatri": {"name": "Jagadhatri", "ott": "zee5_p1"},
    "jaane_anjaane": {"name": "Jaane Anjaane Hum Mile", "ott": "zee5_p1"},
    "greatest_show": {"name": "The Greatest Show on Earth", "ott": "zee5_p1"},
    # DANGAL PLAY
    "pati_anaadi": {"name": "PATI ANAADI", "ott": "dangal_p1"},
    "pati_bhramachari": {"name": "PATI BHRAMACHARI", "ott": "dangal_p1"},
    "mann_atisundar": {"name": "MANN ATISUNDAR", "ott": "dangal_p1"},
    "rimjhim": {"name": "RIMJHIM", "ott": "dangal_p1"},
    "ishq_junooni": {"name": "ISHQ JUNOONI", "ott": "dangal_p1"},
    "tees_ke_paar": {"name": "TEES KE PAAR JAB MILA PYAR", "ott": "dangal_p1"},
    "kaisi_teri": {"name": "KAISI TERI DILLAGI", "ott": "dangal_p1"},
    "mann_sundar": {"name": "MANN SUNDAR", "ott": "dangal_p1"},
    # SONYLIV
    "hui_gumm": {
        "name": "Hui Gumm Yaadein Ek Doctor Do Zindagiyaan",
        "ott": "sonyliv_p1",
    },
    "tmkoc": {"name": "Taarak Mehta Ka Ooltah Chashmah", "ott": "sonyliv_p1"},
    "hastinapur": {"name": "Hastinapur Ke Veer", "ott": "sonyliv_p1"},
    "tum_ho_naa": {"name": "Tum Ho Naa - Ghar Ki Superstar", "ott": "sonyliv_p1"},
    "pushpa": {"name": "Pushpa Impossible", "ott": "sonyliv_p1"},
    "indian_idol": {"name": "Indian Idol", "ott": "sonyliv_p1"},
    "ibd": {"name": "India's Best Dancer", "ott": "sonyliv_p1"},
    "kkk": {"name": "Khatron Ke Khiladi", "ott": "sonyliv_p1"},
    # SUNNXT
    "thodi_si_umeed": {
        "name": "Thodi Si Umeed Thoda Sa Aasman",
        "ott": "sunnxt_p1",
    },
    "divya_prem": {"name": "Divya Prem", "ott": "sunnxt_p1"},
}


def get_all_shows():
  shows = DEFAULT_SHOWS.copy()
  customs = shows_col.find()
  for c in customs:
    shows[c["key"]] = {"name": c["name"], "ott": c["ott"]}
  return shows


def get_all_otts():
  otts = DEFAULT_OTTS.copy()
  customs = ott_col.find()
  for c in customs:
    otts.append((c["name"], c["tag"]))
  return otts


def find_db_doc_by_date(date_str):
  if not date_str:
    return None
  clean_date = date_str.strip().lower()
  if re.match(r"^0\d", clean_date):
    alt_date = re.sub(r"^0(\d)", r"\1", clean_date)
  else:
    alt_date = re.sub(r"^(\d\s)", r"0\1", clean_date)

  return video_col.find_one({
      "$or": [
          {"date": clean_date},
          {"date": alt_date},
          {"date": {"$regex": f"^{clean_date}$", "$options": "i"}},
          {"date": {"$regex": f"^{alt_date}$", "$options": "i"}},
      ]
  })


def extract_ep_and_quality(text):
  ep_match = re.search(r"(?:ep|episode|e)[._\s-]*(\d+)", text, re.IGNORECASE)
  q_match = re.search(r"(\d{3,4}p)", text, re.IGNORECASE)
  ep = ep_match.group(1) if ep_match else "0"
  quality = q_match.group(1).lower() if q_match else "default"
  return ep, quality


def extract_date_from_text(text):
  if not text:
    return None
  months_pattern = r"(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)"
  match = re.search(
      rf"(\d{{1,2}}\s+{months_pattern}(?:\s+\d{{4}})?|\d{{1,2}}[-/.]{months_pattern}[-/.]\d{{2,4}})",
      text,
      re.IGNORECASE,
  )
  if match:
    raw_d = match.group(1)
    if not re.search(r"\d{4}", raw_d):
      raw_d += f" {datetime.now().year}"
    return raw_d.lower().strip()
  return None


def extract_base_title(raw_name):
  clean = re.sub(
      r"[-_.\s]*(TvShowHub|ANTONi|webdlbot|DG_Contents|DG_Content|UtsavTV|Nx-DRM-DL|DS_Ottwebdlbot|kairax007|ottwebdlbot|DKLR_DR|DKLRDR|DKLRShowhub)\b",
      "",
      raw_name,
      flags=re.IGNORECASE,
  )
  match = re.split(
      r"[._\s-]+(?:Season|Episode|Ep|E\d+|\d{3,4}p|Web|Dl|AAC)",
      clean,
      flags=re.IGNORECASE,
  )
  title_part = match[0] if match else clean
  title_part = title_part.replace(".", " ").replace("-", " ").replace("_", " ")
  title_part = re.sub(r"\s+", " ", title_part).strip()
  return title_part.title() if title_part else "Unmatched Show"


def detect_ott_tag(caption):
  text = caption.upper()
  if any(k in text for k in [".ZEE5.", "ZEE5", ".Z5.", " Z5 "]):
    return "zee5_p1"
  elif "SHEMAROO" in text:
    return "shemaroo_p1"
  elif "JIOCINEMA" in text or "JIO" in text:
    return "jiocinema_p1"
  elif any(
      k in text
      for k in [
          "DANGALPLAY",
          "DANGAL",
          ".DP.",
          "PATI.BHRAMACHARI",
          "PATI.ANAADI",
          "MANN.SUNDAR",
          "MANN.ATISUNDAR",
          "RIMJHIM",
          "ISHQ.JUNOONI",
          "TEES.KE.PAAR",
          "KAISI.TERI",
      ]
  ):
    return "dangal_p1"
  elif any(
      k in text
      for k in [
          ".HS.",
          " HS ",
          "HOTSTAR",
          "HS.WEB",
          "STARPLUS",
          "ANUPAMA",
          "YRKKH",
          "UDNE",
          "FEVICREATE",
          "LAUGHTER",
      ]
  ):
    return "hotstar_p1"
  elif any(
      k in text for k in [".SL.", " SONY ", "SONYLIV", ".SL ", "SONY", "SONY.WEB"]
  ):
    return "sonyliv_p1"
  elif "SUNNXT" in text or ".SN." in text:
    return "sunnxt_p1"
  for c in ott_col.find():
    if c["name"].upper() in text:
      return c["tag"]
  return None


def match_show(caption):
  clean_caption = caption.replace("_", " ").replace(".", " ").lower()
  if "shivmay" in clean_caption or "shravan" in clean_caption:
    return "shivmay_shravan"

  exact_map = {
      "mann sundar": "mann_sundar",
      "pati bhramachari": "pati_bhramachari",
      "pati anaadi": "pati_anaadi",
      "mann atisundar": "mann_atisundar",
      "rimjhim": "rimjhim",
      "ishq junooni": "ishq_junooni",
      "tees ke paar": "tees_ke_paar",
      "kaisi teri": "kaisi_teri",
      "shivmay": "shivmay_shravan",
      "parshuram": "parshuram",
      "sairaab": "sairaab",
      "oh humnava": "oh_humnava",
      "humnava": "oh_humnava",
      "yeh rishta": "yrkkh",
      "yrkkh": "yrkkh",
      "mannat": "mannat",
      "juhi mui": "juhi_mui",
      "anupama": "anupama",
      "bareilly": "bareilly",
      "mahadev & sons": "mahadev",
      "mahadev and sons": "mahadev",
      "seher hone": "seher",
      "fevicreate": "fevicreate",
      "udne ki": "udne_ki_aasha",
      "aasha": "udne_ki_aasha",
      "kyunki saas": "kyunki_saas",
      "kyunki rishton": "kyunki_rishton",
      "laughter chefs": "laughter_chefs",
      "binddii": "binddii",
      "aarambhi": "aarambhi",
      "juliet": "juliet",
      "do duniya": "do_duniya",
      "tu hi re": "tu_hi_re",
      "lakshmi nivas": "lakshmi_nivas",
      "tumm se tumm": "tumm_se_tumm",
      "ganga mai": "ganga_mai",
      "vasudha": "vasudha",
      "humari radha": "humari_radha",
      "greatest show": "greatest_show",
      "jagadhatri": "jagadhatri",
      "jaane anjaane": "jaane_anjaane",
      "hui gumm": "hui_gumm",
      "taarak mehta": "tmkoc",
      "tmkoc": "tmkoc",
      "hastinapur": "hastinapur",
      "tum ho naa": "tum_ho_naa",
      "pushpa": "pushpa",
      "indian idol": "indian_idol",
      "best dancer": "ibd",
      "khatron ke khiladi": "kkk",
      "divya prem": "divya_prem",
      "thodi si umeed": "thodi_si_umeed",
  }

  for pattern, s_key in exact_map.items():
    if pattern in clean_caption:
      return s_key
  customs = shows_col.find()
  for c in customs:
    c_name = c["name"].lower().replace("-", " ")
    if len(c_name) > 3 and c_name in clean_caption:
      return c["key"]
  return None


def build_html_caption(raw_name):
  clean_name = (
      raw_name.replace("*", "")
      .replace("<", "&lt;")
      .replace(">", "&gt;")
      .strip()
  )
  base_name = re.sub(
      r"\.(mp4|mkv|avi|mov|webm|flv)$", "", clean_name, flags=re.IGNORECASE
  )
  base_name = re.sub(
      r"[-_.\s]+(TvShowHub|ANTONi|webdlbot|DG_Contents|DG_Content|UtsavTV|Nx-DRM-DL|DS_Ottwebdlbot|kairax007|ottwebdlbot|DKLR_DR|DKLRDR|DKLRShowhub)[-_.\s]*$",
      "",
      base_name,
      flags=re.IGNORECASE,
  )
  base_name = re.sub(r"[-_]+[a-zA-Z0-9]+$", "", base_name)
  final_filename = f"{base_name.strip('.-_')}.DKLRShowhub.mp4"

  return (
      f"📄 <b>{final_filename}</b>\n\n"
      "⚡️ <b>Join :-</b> [ <b>@DKLRShowhub</b> ]\n\n"
      '📌 <b>Join:</b> <a'
      ' href="https://t.me/+AT1UIPpK3c04MTk1">https://t.me/+AT1UIPpK3c04MTk1</a>\n\n'
      '📌 <b>Upcoming New Episode -</b> <a'
      ' href="https://t.me/+sN83w5txQO9hNTdl">https://t.me/+sN83w5txQO9hNTdl</a>'
  )


# ----------------- FFmpeg Delogo Watermark Remover -----------------
def remove_watermark_ffmpeg(input_path, output_path):
  cmd = [
      "ffmpeg",
      "-i",
      input_path,
      "-vf",
      "delogo=x=30:y=H-160:w=320:h=120",
      "-c:v",
      "libx264",
      "-preset",
      "ultrafast",
      "-crf",
      "23",
      "-c:a",
      "copy",
      output_path,
      "-y",
  ]
  subprocess.run(cmd, check=True)


# ----------------- AUTO SAVE TO DB LOGIC -----------------
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
      video_col.update_one(
          {"_id": doc["_id"]},
          {"$set": {"date": target_date, "shows": existing_shows}},
      )
    return matched_key, True
  return None, False


# ----------------- BATCH FORWARD & CLEAN LOGIC -----------------
async def process_batch_from_id(
    chat_id, start_msg_id, target_id, reply_chat_id, context
):
  global pyrogram_userbot
  if not pyrogram_userbot:
    await context.bot.send_message(
        chat_id=reply_chat_id,
        text="❌ <b>UserBot एक्टिव नहीं है! SESSION_STRING चेक करें।</b>",
        parse_mode="HTML",
    )
    return

  await context.bot.send_message(
      chat_id=reply_chat_id,
      text=(
          f"🚀 <b>Batch Cleaner शुरू!</b>\n👉 मैसेज ID <code>{start_msg_id}</code> के"
          " बाद की सभी वीडियोज वॉटरमार्क हटकर टारगेट चैनल और डेटाबेस में ऐड"
          " होंगी..."
      ),
      parse_mode="HTML",
  )

  processed_count = 0
  try:
    async for message in pyrogram_userbot.get_chat_history(chat_id):
      if message.id < start_msg_id:
        break

      if message.video or message.document:
        input_file = None
        output_file = None
        raw_name = (
            message.caption
            or (message.video and message.video.file_name)
            or (message.document and message.document.file_name)
            or "Episode_Video.mp4"
        )
        msg_date = extract_date_from_text(raw_name)

        try:
          input_file = await message.download()
          output_file = f"clean_{os.path.basename(input_file)}"

          loop = asyncio.get_running_loop()
          await loop.run_in_executor(
              None, remove_watermark_ffmpeg, input_file, output_file
          )

          # Your Custom Caption Added
          custom_caption = build_html_caption(raw_name)
          sent_msg = await pyrogram_userbot.send_document(
              chat_id=target_id, document=output_file, caption=custom_caption
          )
          processed_count += 1

          clean_file_id = (
              sent_msg.document.file_id
              if sent_msg.document
              else sent_msg.video.file_id
          )

          # Auto Save to DB if Date Exists
          if msg_date:
            matched_key, is_saved = auto_save_file_to_db(
                clean_file_id, raw_name, msg_date
            )
            if not is_saved:
              base_t = extract_base_title(raw_name)
              btn = InlineKeyboardMarkup([[
                  InlineKeyboardButton(
                      f"➕ Add '{base_t}'", callback_data="btn_add_show"
                  )
              ]])
              await context.bot.send_message(
                  chat_id=reply_chat_id,
                  text=(
                      f"🚨 <b>Unmatched Show!</b>\n🎬 <b>Title:</b> {base_t}\n📅"
                      f" <b>Date:</b> {msg_date.title()}\n👇 शो जोड़ने के लिए"
                      " नीचे दबाएँ:"
                  ),
                  reply_markup=btn,
                  parse_mode="HTML",
              )
          else:
            # Date Missing Prompt
            if "missing_date_vids" not in context.user_data:
              context.user_data["missing_date_vids"] = []
            context.user_data["missing_date_vids"].append(
                {"id": clean_file_id, "raw_name": raw_name}
            )
            context.user_data["awaiting_missing_date"] = True
            await context.bot.send_message(
                chat_id=reply_chat_id,
                text=(
                    f"⚠️ <b>तारीख नहीं मिली!</b>\n🎬 <b>File:</b> {raw_name}\n\n✍️"
                    " <b>कृपया इस वीडियो के लिए तारीख लिखकर भेजें (उदा: 16"
                    " August 2026):</b>"
                ),
                parse_mode="HTML",
            )

        except Exception as e:
          print(f"⚠️ [Batch File Error]: {e}")
        finally:
          if input_file and os.path.exists(input_file):
            os.remove(input_file)
          if output_file and os.path.exists(output_file):
            os.remove(output_file)

    await context.bot.send_message(
        chat_id=reply_chat_id,
        text=(
            f"🎉 <b>Batch Complete!</b>\n✅ कुल <b>{processed_count} वीडियोस</b>"
            " आपके कस्टम टाइटल के साथ टारगेट चैनल पर भेज दी गई हैं।"
        ),
        parse_mode="HTML",
    )
  except Exception as e:
    print(f"❌ [Batch Error]: {e}")


def get_main_menu_keyboard():
  settings = get_bot_settings()
  rec_status = (
      "🟢 Auto Receive: ON"
      if settings.get("auto_receive", True)
      else "🔴 Auto Receive: OFF"
  )
  send_status = (
      "🟢 Auto Send: ON"
      if settings.get("auto_send", True)
      else "🔴 Auto Send: OFF"
  )
  src_name = settings.get("source_channel_name", "Not Set")
  tgt_name = settings.get("target_channel_name", "Not Set")

  buttons = [
      [
          InlineKeyboardButton("➕ Add New Show", callback_data="btn_add_show"),
          InlineKeyboardButton("➕ Add New OTT", callback_data="btn_add_ott"),
      ],
      [
          InlineKeyboardButton(rec_status, callback_data="toggle_auto_receive"),
          InlineKeyboardButton(send_status, callback_data="toggle_auto_send"),
      ],
      [
          InlineKeyboardButton(
              f"📥 Source: {src_name}", callback_data="btn_set_receive_channel"
          )
      ],
      [
          InlineKeyboardButton(
              f"📤 Target: {tgt_name}", callback_data="btn_set_send_channel"
          )
      ],
      [
          InlineKeyboardButton(
              "⚡️ Start Batch From Forwarded Msg",
              callback_data="btn_start_batch",
          )
      ],
  ]
  return InlineKeyboardMarkup(buttons)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if update.message:
    update_bot_setting("admin_chat_id", update.effective_chat.id)
    await update.message.reply_text(
        "<b>नमस्ते भाई! DKLR Show Hub Engine Live!</b>\n\n"
        "👉 सोर्स चैनल की सभी वीडियोज वॉटरमार्क हटकर, आपका कस्टम टाइटल लगकर सीधे"
        " टारगेट चैनल पर जाएँगी।\n"
        "👉 तारीख मिलने पर डेटाबेस में अपने आप ऐड होगी, न मिलने पर बॉट आपसे तारीख"
        " माँगेगा।\n\n"
        "👇 <b>कंट्रोल पैनल:</b>",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML",
    )


# ----------------- MESSAGE & FORWARD HANDLER -----------------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if not update.message:
    return

  msg = update.message
  text = (msg.text or "").strip()

  # 1. MISSING DATE HANDLER
  if context.user_data.get("awaiting_missing_date"):
    target_date = text.lower().strip()
    context.user_data["awaiting_missing_date"] = False
    missing_list = context.user_data.get("missing_date_vids", [])
    context.user_data["missing_date_vids"] = []

    for item in missing_list:
      auto_save_file_to_db(item["id"], item["raw_name"], target_date)

    await msg.reply_text(
        f"✅ <b>तारीख सेट हो गई:</b> <b>{target_date.title()}</b>\n📁"
        f" कुल <b>{len(missing_list)} वीडियोस</b> डेटाबेस में सेव कर दी गई हैं!",
        parse_mode="HTML",
    )
    return

  # 2. BATCH FORWARD RECEIVER
  if context.user_data.get("awaiting_batch_forward"):
    if msg.forward_from_chat and msg.forward_from_message_id:
      source_chat_id = msg.forward_from_chat.id
      start_id = msg.forward_from_message_id
      settings = get_bot_settings()
      target_id = settings.get("target_channel_id")

      if not target_id:
        await msg.reply_text(
            "❌ <b>कृपया पहले 'Target Channel' सेट करें!</b>", parse_mode="HTML"
        )
        return

      context.user_data["awaiting_batch_forward"] = False
      asyncio.create_task(
          process_batch_from_id(
              source_chat_id,
              start_id,
              target_id,
              update.effective_chat.id,
              context,
          )
      )
      return

  # 3. SET SOURCE CHANNEL
  if context.user_data.get("setting_receive_channel"):
    ch_id = None
    ch_title = None
    if msg.forward_from_chat:
      ch_id = msg.forward_from_chat.id
      ch_title = (
          msg.forward_from_chat.title
          or msg.forward_from_chat.username
          or str(ch_id)
      )
    elif text:
      ch_title = text.replace("https://t.me/", "").replace("@", "").strip()
      ch_id = ch_title

    if ch_id:
      update_bot_setting("source_channel_id", ch_id)
      update_bot_setting("source_channel_name", ch_title)
      context.user_data["setting_receive_channel"] = False
      await msg.reply_text(
          f"🎯 <b>Source Channel सेट हो गया:</b> <code>{ch_title}</code>\n🆔"
          f" <b>Channel ID:</b> <code>{ch_id}</code>",
          reply_markup=get_main_menu_keyboard(),
          parse_mode="HTML",
      )
      return

  # 4. SET TARGET CHANNEL
  if context.user_data.get("setting_send_channel"):
    target_id = None
    target_title = None
    if msg.forward_from_chat:
      target_id = msg.forward_from_chat.id
      target_title = (
          msg.forward_from_chat.title
          or msg.forward_from_chat.username
          or str(target_id)
      )
    elif text:
      target_title = (
          "@" + text.replace("https://t.me/", "").replace("@", "").strip()
      )
      target_id = target_title

    if target_id:
      update_bot_setting("target_channel_id", target_id)
      update_bot_setting("target_channel_name", target_title)
      context.user_data["setting_send_channel"] = False
      await msg.reply_text(
          f"🎯 <b>Target Channel सेट हो गया:</b> <code>{target_title}</code>\n🆔"
          f" <b>Target ID:</b> <code>{target_id}</code>",
          reply_markup=get_main_menu_keyboard(),
          parse_mode="HTML",
      )
      return

  # 5. ADD NEW SHOW STEP 1
  if context.user_data.get("adding_new_show_step1"):
    show_name = text.strip().title()
    show_key = show_name.lower().replace(" ", "_")
    context.user_data["temp_show_name"] = show_name
    context.user_data["temp_show_key"] = show_key
    context.user_data["adding_new_show_step1"] = False

    all_otts = get_all_otts()
    ott_buttons = [
        [InlineKeyboardButton(o_name, callback_data=f"save_show_ott|{o_tag}")]
        for o_name, o_tag in all_otts
    ]
    await msg.reply_text(
        f"🎬 <b>Show Name:</b> {show_name}\n\n👇 <b>OTT चुनें:</b>",
        reply_markup=InlineKeyboardMarkup(ott_buttons),
        parse_mode="HTML",
    )
    return

  # 6. ADD NEW OTT NAME
  if context.user_data.get("adding_new_ott_mode"):
    ott_name = text.strip()
    ott_tag = ott_name.lower().replace(" ", "") + "_p1"
    ott_col.update_one(
        {"tag": ott_tag}, {"$set": {"name": ott_name, "tag": ott_tag}}, upsert=True
    )
    context.user_data["adding_new_ott_mode"] = False
    await msg.reply_text(
        f"✅ <b>नया OTT जोड़ा गया:</b> {ott_name}", parse_mode="HTML"
    )
    return

  # 7. USER SEARCHING DATE
  months = [
      "january",
      "february",
      "march",
      "april",
      "may",
      "june",
      "july",
      "august",
      "september",
      "october",
      "november",
      "december",
  ]
  if any(m in text.lower() for m in months) and re.search(r"\d+", text):
    user_input_date = text.lower().strip()
    user = update.effective_user
    username = (user.username or "").lower()

    today_dt = datetime.now()
    today_fmt1 = today_dt.strftime("%d %B %Y").lower()
    today_fmt2 = today_dt.strftime("%-d %B %Y").lower()
    clean_user_input = re.sub(r"^0(\d)", r"\1", user_input_date)
    clean_today = re.sub(r"^0(\d)", r"\1", today_fmt1)

    if (
        clean_user_input == clean_today
        or user_input_date in [today_fmt1, today_fmt2]
    ) and username != OWNER_USERNAME:
      channel_btn = InlineKeyboardMarkup([[
          InlineKeyboardButton(
              "🚀 Main Channel", url="https://t.me/+AT1UIPpK3c04MTk1"
          )
      ]])
      await msg.reply_text(
          "🚫 <b>माफ़ कीजिए! आप आज की एपिसोड यहां नहीं देख सकते।</b>\n👉"
          " <b>कृपया हमारे मुख्य चैनल पर जाएं।</b>",
          reply_markup=channel_btn,
          parse_mode="HTML",
      )
      return

    context.user_data["active_date"] = user_input_date
    all_shows = get_all_shows()
    doc = find_db_doc_by_date(user_input_date)
    uploaded_shows_dict = doc.get("shows", {}) if doc else {}

    uploaded_ott_tags = set()
    for s_key, vid_list in uploaded_shows_dict.items():
      if len(vid_list) > 0 and s_key in all_shows:
        uploaded_ott_tags.add(all_shows[s_key]["ott"])

    all_otts = get_all_otts()
    buttons = [
        [InlineKeyboardButton(o_name, callback_data=f"o|{o_tag}")]
        for o_name, o_tag in all_otts
        if o_tag in uploaded_ott_tags
    ]

    if buttons:
      buttons.append([InlineKeyboardButton("❌ Close", callback_data="close")])
      await msg.reply_text(
          "✅ <b>Data fetched successfully!</b>\n\n"
          f"📅 <b>Date Requested:</b>\n<b>{text.title()}</b>\n\n"
          "🔍 <b>Please choose your desired OTT below:</b>",
          reply_markup=InlineKeyboardMarkup(buttons),
          parse_mode="HTML",
      )
    else:
      await msg.reply_text(
          f"❌ <b>इस तारीख ({text.title()}) में कोई भी वीडियो उपलब्ध नहीं"
          " है!</b>",
          parse_mode="HTML",
      )


async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  await query.answer()
  data = query.data

  if data == "close":
    await query.message.delete()
    return

  elif data == "toggle_auto_receive":
    settings = get_bot_settings()
    new_val = not settings.get("auto_receive", True)
    update_bot_setting("auto_receive", new_val)
    await query.message.edit_reply_markup(reply_markup=get_main_menu_keyboard())
    return

  elif data == "toggle_auto_send":
    settings = get_bot_settings()
    new_val = not settings.get("auto_send", True)
    update_bot_setting("auto_send", new_val)
    await query.message.edit_reply_markup(reply_markup=get_main_menu_keyboard())
    return

  elif data == "btn_set_receive_channel":
    context.user_data["setting_receive_channel"] = True
    await query.message.reply_text(
        "📥 <b>सोर्स चैनल से कोई भी एक मैसेज Forward करें:</b>",
        parse_mode="HTML",
    )
    return

  elif data == "btn_set_send_channel":
    context.user_data["setting_send_channel"] = True
    await query.message.reply_text(
        "📤 <b>टारगेट चैनल से कोई भी एक मैसेज Forward करें:</b>",
        parse_mode="HTML",
    )
    return

  elif data == "btn_start_batch":
    context.user_data["awaiting_batch_forward"] = True
    await query.message.reply_text(
        "⚡️ <b>Batch Cleaner Active!</b>\n\n👉 सोर्स चैनल से वह <b>SMS या Video"
        " Forward करें</b> जहाँ से प्रोसेस शुरू करना चाहते हैं।\nबॉट उस मैसेज के"
        " नीचे की <b>सभी वीडियोस</b> को वॉटरमार्क हटाकर आपके कस्टम टाइटल के साथ"
        " टारगेट चैनल पर भेज देगा!",
        parse_mode="HTML",
    )
    return

  elif data == "btn_add_show":
    context.user_data["adding_new_show_step1"] = True
    await query.message.reply_text(
        "✍️ <b>कृपया नए शो का नाम लिखकर भेजें:</b>", parse_mode="HTML"
    )
    return

  elif data == "btn_add_ott":
    context.user_data["adding_new_ott_mode"] = True
    await query.message.reply_text(
        "✍️ <b>कृपया नए OTT प्लेटफ़ॉर्म का नाम लिखकर भेजें:</b>",
        parse_mode="HTML",
    )
    return

  elif data.startswith("save_show_ott|"):
    ott_tag = data.split("|")[1]
    show_name = context.user_data.get("temp_show_name")
    show_key = context.user_data.get("temp_show_key")
    shows_col.update_one(
        {"key": show_key},
        {"$set": {"key": show_key, "name": show_name, "ott": ott_tag}},
        upsert=True,
    )
    await query.message.reply_text(
        f"✅ <b>नया शो सफलतापूर्वक डेटाबेस में जोड़ा गया!</b>\n\n🎬 <b>Show"
        f" Name:</b> {show_name}\n📺 <b>OTT Tag:</b>"
        f" {ott_tag.split('_')[0].upper()}",
        parse_mode="HTML",
    )
    return

  user_date = context.user_data.get("active_date", "")
  if not user_date and query.message and query.message.text:
    match = re.search(
        r"Date Requested:\s*\n*([^\n]+)", query.message.text, re.IGNORECASE
    )
    if not match:
      match = re.search(
          r"Chosen Date:\s*<b>(.+?)</b>", query.message.text, re.IGNORECASE
      )
    if match:
      user_date = match.group(1).strip().lower()

  if data.startswith("o|"):
    ott_tag = data.split("|")[1]
    all_shows = get_all_shows()
    doc = find_db_doc_by_date(user_date)
    uploaded_shows_dict = doc.get("shows", {}) if doc else {}

    show_buttons = []
    for key, info in all_shows.items():
      if info["ott"] == ott_tag:
        if key in uploaded_shows_dict and len(uploaded_shows_dict[key]) > 0:
          show_buttons.append([
              InlineKeyboardButton(
                  f"{info['name']} ↗️", callback_data=f"s|{key}"
              )
          ])

    disp_date = user_date.title() if user_date else "Selected Date"
    if show_buttons:
      show_buttons.append([
          InlineKeyboardButton("⬅️ Choose OTT", callback_data="b_ott"),
          InlineKeyboardButton("❌ Close", callback_data="close"),
      ])
      await query.message.edit_text(
          f"🎬 <b>{ott_tag.split('_')[0].upper()} Shows</b>\n\n📅 <b>Chosen"
          f" Date:</b> <b>{disp_date}</b>\n\n🎯 <b>Available Shows Below:</b>",
          reply_markup=InlineKeyboardMarkup(show_buttons),
          parse_mode="HTML",
      )

  elif data == "b_ott":
    all_shows = get_all_shows()
    doc = find_db_doc_by_date(user_date)
    uploaded_shows_dict = doc.get("shows", {}) if doc else {}

    uploaded_ott_tags = set()
    for s_key, vid_list in uploaded_shows_dict.items():
      if len(vid_list) > 0 and s_key in all_shows:
        uploaded_ott_tags.add(all_shows[s_key]["ott"])

    all_otts = get_all_otts()
    buttons = [
        [InlineKeyboardButton(o_name, callback_data=f"o|{o_tag}")]
        for o_name, o_tag in all_otts
        if o_tag in uploaded_ott_tags
    ]
    buttons.append([InlineKeyboardButton("❌ Close", callback_data="close")])

    disp_date = user_date.title() if user_date else "Selected Date"
    await query.message.edit_text(
        "✅ <b>Data fetched successfully!</b>\n\n"
        f"📅 <b>Date Requested:</b>\n<b>{disp_date}</b>\n\n"
        "🔍 <b>Please choose your desired OTT below:</b>",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML",
    )

  elif data.startswith("s|"):
    show_key = data.split("|")[1]
    doc = find_db_doc_by_date(user_date)
    date_db = doc.get("shows", {}) if doc else {}
    video_list = date_db.get(show_key, [])

    if video_list:
      sent_messages = []
      for vid_obj in video_list:
        r_name = vid_obj.get("raw_name", "Episode_Video.DKLRShowhub.mp4")
        fresh_caption = build_html_caption(r_name)
        sent_vid = await context.bot.send_document(
            chat_id=query.message.chat_id,
            document=vid_obj["id"],
            caption=fresh_caption,
            parse_mode="HTML",
        )
        sent_messages.append(sent_vid.message_id)

      notice_text = (
          "╭─────── ‼️ <b>Auto-Delete Notice</b> ‼️ ───────╮\n\n"
          "🚨 <b>Make sure to save the video!</b>\n"
          "⏰ <b>Videos Will Be Auto-deleted After 60 minutes to avoid copyright"
          " issue</b> ⌛\n"
          "📬 <b>Forward it to Saved Messages and Watch there</b>\n\n"
          "╰────────────────────────────────────╯"
      )
      sent_notice = await context.bot.send_message(
          chat_id=query.message.chat_id,
          text=notice_text,
          parse_mode="HTML",
      )
      sent_messages.append(sent_notice.message_id)

      async def auto_delete_task(chat_id, msg_ids):
        await asyncio.sleep(3600)
        for mid in msg_ids:
          try:
            await context.bot.delete_message(chat_id=chat_id, message_id=mid)
          except Exception:
            pass

      asyncio.create_task(
          auto_delete_task(query.message.chat_id, sent_messages)
      )


# ----------------- BACKGROUND USERBOT RUNNER (LIVE SYNC) -----------------
async def start_userbot():
  global pyrogram_userbot, tg_bot_app
  if not SESSION_STRING:
    print("⚠️ [UserBot] SESSION_STRING missing! UserBot inactive.")
    return

  pyrogram_userbot = Client(
      "dklr_userbot",
      api_id=API_ID,
      api_hash=API_HASH,
      session_string=SESSION_STRING,
  )

  @pyrogram_userbot.on_message(filters.video | filters.document)
  async def on_new_video(client, message):
    settings = get_bot_settings()
    if not settings.get("auto_receive", True):
      return

    saved_src_id = settings.get("source_channel_id")
    if not saved_src_id:
      return

    if str(saved_src_id) != str(message.chat.id) and str(
        saved_src_id
    ).lower() != (message.chat.username or "").lower():
      return

    input_file = None
    output_file = None
    target_dest = settings.get("target_channel_id")
    admin_id = settings.get("admin_chat_id")

    raw_name = (
        message.caption
        or (message.video and message.video.file_name)
        or (message.document and message.document.file_name)
        or "Episode_Video.mp4"
    )
    msg_date = extract_date_from_text(raw_name)

    try:
      input_file = await message.download()
      output_file = f"clean_{os.path.basename(input_file)}"

      loop = asyncio.get_running_loop()
      await loop.run_in_executor(
          None, remove_watermark_ffmpeg, input_file, output_file
      )

      # 1. Direct Forward to Target Channel with YOUR Caption
      clean_file_id = None
      if settings.get("auto_send", True) and target_dest:
        custom_caption = build_html_caption(raw_name)
        sent_m = await client.send_document(
            chat_id=target_dest, document=output_file, caption=custom_caption
        )
        clean_file_id = (
            sent_m.document.file_id if sent_m.document else sent_m.video.file_id
        )

      # 2. Database Sync & Admin Alerts
      if clean_file_id:
        if msg_date:
          matched_key, is_saved = auto_save_file_to_db(
              clean_file_id, raw_name, msg_date
          )
          if not is_saved and admin_id and tg_bot_app:
            base_t = extract_base_title(raw_name)
            btn = InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    f"➕ Add '{base_t}'", callback_data="btn_add_show"
                )
            ]])
            await tg_bot_app.bot.send_message(
                chat_id=admin_id,
                text=(
                    f"🚨 <b>Unmatched Show Live!</b>\n🎬 <b>Title:</b>"
                    f" {base_t}\n📁 <b>Auto Date:</b> {msg_date.title()}\n👇"
                    " नीचे दिए बटन से इसे शो लिस्ट में जोड़ें:"
                ),
                reply_markup=btn,
                parse_mode="HTML",
            )
        else:
          # Date missing in live video: Ask admin for date
          if admin_id and tg_bot_app:
            await tg_bot_app.bot.send_message(
                chat_id=admin_id,
                text=(
                    f"⚠️ <b>लाइव वीडियो में तारीख नहीं मिली!</b>\n🎬"
                    f" <b>File:</b> {raw_name}\n\n✍️ <b>कृपया तारीख लिखकर भेजें"
                    " (उदा: 16 August 2026):</b>"
                ),
                parse_mode="HTML",
            )
    except Exception as e:
      print(f"⚠️ [Live Video Error]: {e}")
    finally:
      if input_file and os.path.exists(input_file):
        os.remove(input_file)
      if output_file and os.path.exists(output_file):
        os.remove(output_file)

  try:
    print("🚀 [UserBot] Starting Engine...")
    await pyrogram_userbot.start()
    print("✅ [UserBot] Active & Listening!")
  except Exception as e:
    print(f"⚠️ UserBot Error: {e}")


def main():
  global tg_bot_app
  loop = asyncio.new_event_loop()
  asyncio.set_event_loop(loop)
  loop.create_task(start_userbot())

  tg_bot_app = ApplicationBuilder().token(BOT_TOKEN).build()
  tg_bot_app.add_handler(CommandHandler("start", start_command))
  tg_app = tg_bot_app
  tg_app.add_handler(
      MessageHandler(
          tg_filters.VIDEO | tg_filters.Document.VIDEO, handle_video_upload
      )
  )
  tg_app.add_handler(
      MessageHandler(
          (tg_filters.TEXT | tg_filters.FORWARDED) & ~tg_filters.COMMAND,
          handle_text,
      )
  )
  tg_app.add_handler(CallbackQueryHandler(button_click))

  print("DKLR Show Hub Bot Engine Live...")
  tg_app.run_polling(close_loop=False)


if __name__ == "__main__":
  main()

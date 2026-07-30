import asyncio
import os
import re
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

# ----------------- FLASK SERVER FOR RENDER -----------------
app_flask = Flask(__name__)


@app_flask.route("/")
def home():
  return "DKLR TV Bot Dynamic Auto-Show Engine Active!"


def run_flask():
  port = int(os.environ.get("PORT", 8080))
  app_flask.run(host="0.0.0.0", port=port)


def keep_alive():
  t = Thread(target=run_flask)
  t.start()


keep_alive()

# ----------------- CONFIG & MONGODB SETUP -----------------
BOT_TOKEN = "8909033238:AAHiDgwzXyNCRplZ8GTEGvTJJyrGS7kX20o"
MONGO_URI = os.environ.get(
    "MONGO_URI",
    "mongodb+srv://deepakkumar451811_db_user:z0gBb13CSvYAECgG@cluster0.osysn1c.mongodb.net/?appName=Cluster0",
)

API_ID = int(os.environ.get("API_ID", "30366893"))
API_HASH = os.environ.get("API_HASH", "ecb01a29588b13c36c8c373584270ea8")
TARGET_BOT_USERNAME = "@autofiltertsh_bot"
SOURCE_CHANNELS = ["tvshowhubb"]

client = pymongo.MongoClient(MONGO_URI)
db = client["dklr_bot_db"]
video_col = db["videos"]
shows_col = db["custom_shows"]

# ----------------- MASTER SHOWS DATABASE -----------------
DEFAULT_SHOWS = {
    # HOTSTAR SHOWS
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
    # ZEE5 SHOWS
    "tu_hi_re": {"name": "Tu Hi Re Dil Mein", "ott": "zee5_p1"},
    "lakshmi_nivas": {"name": "Lakshmi Nivas", "ott": "zee5_p1"},
    "tumm_se_tumm": {"name": "Tumm Se Tumm Tak", "ott": "zee5_p1"},
    "ganga_mai": {"name": "Ganga Mai Ki Betiyan", "ott": "zee5_p1"},
    "vasudha": {"name": "Vasudha", "ott": "zee5_p1"},
    "humari_radha": {"name": "Humari Radha", "ott": "zee5_p1"},
    "jagadhatri": {"name": "Jagadhatri", "ott": "zee5_p1"},
    "jaane_anjaane": {"name": "Jaane Anjaane Hum Mile", "ott": "zee5_p1"},
    "greatest_show": {"name": "The Greatest Show on Earth", "ott": "zee5_p1"},
    # DANGAL PLAY SHOWS
    "pati_anaadi": {"name": "PATI ANAADI", "ott": "dangal_p1"},
    "pati_bhramachari": {"name": "PATI BHRAMACHARI", "ott": "dangal_p1"},
    "mann_atisundar": {"name": "MANN ATISUNDAR", "ott": "dangal_p1"},
    "rimjhim": {"name": "RIMJHIM", "ott": "dangal_p1"},
    "ishq_junooni": {"name": "ISHQ JUNOONI", "ott": "dangal_p1"},
    "tees_ke_paar": {"name": "TEES KE PAAR JAB MILA PYAR", "ott": "dangal_p1"},
    "kaisi_teri": {"name": "KAISI TERI DILLAGI", "ott": "dangal_p1"},
    "mann_sundar": {"name": "MANN SUNDAR", "ott": "dangal_p1"},
    # SONYLIV SHOWS
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
    # SUNNXT SHOWS
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


def detect_ott_tag(caption):
  text = caption.upper()
  if (
      ".HS." in text
      or " HS " in text
      or "HOTSTAR" in text
      or "HS.WEB" in text
      or "HOTSTAR" in text
  ):
    return "hotstar_p1"
  elif (
      ".Z5." in text
      or " Z5 " in text
      or "ZEE5" in text
      or ".ZEE." in text
      or "ZEE" in text
  ):
    return "zee5_p1"
  elif (
      ".SL." in text
      or " SONY " in text
      or "SONYLIV" in text
      or ".SL " in text
      or "SONY" in text
  ):
    return "sonyliv_p1"
  elif (
      ".DP." in text
      or " DANGAL " in text
      or "DANGALPLAY" in text
      or "DANGAL" in text
  ):
    return "dangal_p1"
  elif "SUNNXT" in text or ".SN." in text:
    return "sunnxt_p1"
  return "hotstar_p1"


def extract_show_title_auto(raw_name):
  clean = (
      raw_name.replace("TvShowHub", "")
      .replace("tvshowhub", "")
      .replace("DKLRDR", "")
      .replace("DKLR_DR", "")
  )
  clean_text = clean.replace(".", " ").replace("_", " ")

  parts = clean_text.split()
  title_part = parts[0] if parts else "Auto Show"
  title_part = re.sub(
      r"(Season|Episode|Ep|E\d+|\d+)", "", title_part, flags=re.IGNORECASE
  ).strip()
  if not title_part or len(title_part) < 3:
    title_part = "Auto Show " + raw_name[:8]
  return title_part.title()


def match_show(caption):
  clean_caption = caption.replace("_", " ").replace(".", " ").lower()

  key_map = {
      "mann sundar": "mann_sundar",
      "pati bhramachari": "pati_bhramachari",
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
      "mahadev": "mahadev",
      "seher hone": "seher",
      "fevicreate": "fevicreate",
      "tu hi re": "tu_hi_re",
      "lakshmi nivas": "lakshmi_nivas",
      "mann atisundar": "mann_atisundar",
      "atisundar": "mann_atisundar",
      "hui gumm": "hui_gumm",
      "divya prem": "divya_prem",
      "thodi si umeed": "thodi_si_umeed",
      "aarambhi": "aarambhi",
      "tumm se tumm": "tumm_se_tumm",
      "rimjhim": "rimjhim",
      "taarak mehta": "tmkoc",
      "tmkoc": "tmkoc",
      "ganga mai": "ganga_mai",
      "hastinapur": "hastinapur",
      "ishq junooni": "ishq_junooni",
      "vasudha": "vasudha",
      "humari radha": "humari_radha",
      "tees ke paar": "tees_ke_paar",
      "pushpa impossible": "pushpa",
      "greatest show": "greatest_show",
      "jagadhatri": "jagadhatri",
      "indian idol": "indian_idol",
      "kaisi teri": "kaisi_teri",
      "kyunki saas": "kyunki_saas",
      "kyunki rishton": "kyunki_rishton",
      "jaane anjaane": "jaane_anjaane",
      "best dancer": "ibd",
      "pati anaadi": "pati_anaadi",
      "udne ki": "udne_ki_aasha",
      "laughter chefs": "laughter_chefs",
      "binddii": "binddii",
  }

  for pattern, s_key in key_map.items():
    if pattern in clean_caption:
      return s_key

  all_shows = get_all_shows()
  for s_key, data in all_shows.items():
    name_clean = data["name"].lower().replace("-", " ")
    words = [w for w in name_clean.split() if len(w) > 3]
    if any(w in clean_caption for w in words):
      return s_key

  return None


def build_html_caption(raw_name):
  cleaned_name = (
      raw_name.replace("TvShowHub", "DKLRDR")
      .replace("tvshowhub", "DKLRDR")
      .replace("DKLR_DR", "DKLRDR")
  )
  cleaned_name = (
      cleaned_name.replace("*", "")
      .replace("<", "&lt;")
      .replace(">", "&gt;")
      .strip()
  )

  if not cleaned_name:
    cleaned_name = "Episode_Video.DKLRDR.mp4"

  return (
      f"<b>{cleaned_name}</b>\n\n"
      "⚡️ <b>Join :-</b> [ <b>@DKLRDR</b> ]\n\n"
      '📌 <b>Join:</b> <a'
      ' href="https://t.me/+AT1UIPpK3c04MTk1">https://t.me/+AT1UIPpK3c04MTk1</a>\n\n'
      '📌 <b>Upcoming New Episode -</b> <a'
      ' href="https://t.me/+sN83w5txQO9hNTdl">https://t.me/+sN83w5txQO9hNTdl</a>'
  )


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if update.message:
    await update.message.reply_text(
        "<b>नमस्ते भाई! कृपया कोई तारीख लिखकर भेजें (जैसे: 25 July 2026)।</b>",
        parse_mode="HTML",
    )


async def handle_video_upload(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
  if update.message and update.message.video:
    file_id = update.message.video.file_id
    raw_name = (
        update.message.caption or update.message.video.file_name or ""
    )

    if "pending_videos" not in context.user_data:
      context.user_data["pending_videos"] = []

    context.user_data["pending_videos"].append({
        "id": file_id,
        "raw_name": raw_name,
    })
    context.user_data["awaiting_upload_date"] = True

    total_rec = len(context.user_data["pending_videos"])
    await update.message.reply_text(
        f"🎥 <b>वीडियो प्राप्त हो गई! (कुल: {total_rec})</b>\n\n"
        "✍️ <b>कृपया तारीख लिखकर भेजें (जैसे: 25 July 2026):</b>",
        parse_mode="HTML",
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if not update.message or not update.message.text:
    return

  text = update.message.text.strip()

  # 📌 अगर मैनुअल शो ऐड करने का मोड ऑन है
  if context.user_data.get("adding_manual_show"):
    vid_data = context.user_data.get("manual_vid")
    target_date = context.user_data.get("manual_date")
    ott_tag = context.user_data.get("manual_ott")

    show_name = text.title()
    show_key = show_name.lower().replace(" ", "_")

    # DB में नया बटन सेव करें
    shows_col.update_one(
        {"key": show_key},
        {"$set": {"key": show_key, "name": show_name, "ott": ott_tag}},
        upsert=True,
    )

    # वीडियो को उस तारीख में सेव करें
    doc = video_col.find_one({"date": target_date})
    existing_shows = doc.get("shows", {}) if doc else {}
    ex_list = existing_shows.get(show_key, [])

    ex_list.append({"id": vid_data["id"], "raw_name": vid_data["raw_name"]})
    existing_shows[show_key] = ex_list

    if not doc:
      video_col.insert_one({"date": target_date, "shows": existing_shows})
    else:
      video_col.update_one(
          {"date": target_date}, {"$set": {"shows": existing_shows}}
      )

    context.user_data["adding_manual_show"] = False
    await update.message.reply_text(
        f"✅ <b>नया शो सफ़लतापूर्वक ऐड हो गया!</b>\n\n"
        f"🎬 <b>Show Name:</b> {show_name}\n"
        f"📺 <b>OTT:</b> {ott_tag.split('_')[0].upper()}\n"
        f"📅 <b>Date:</b> {target_date.title()}\n\n"
        "🎉 <b>बटन ऑटोमैटिक बन गया है और वीडियो सेव हो गई है!</b>",
        parse_mode="HTML",
    )
    return

  # 📌 नॉर्मल वीडियो प्रोसेसिंग
  if context.user_data.get("awaiting_upload_date"):
    target_date = text.lower()
    context.user_data["awaiting_upload_date"] = False

    pending = context.user_data.get("pending_videos", [])
    context.user_data["pending_videos"] = []

    auto_saved = 0
    duplicate_count = 0
    unmatched_list = []

    doc = video_col.find_one({"date": target_date})
    existing_shows = doc.get("shows", {}) if doc else {}

    for vid in pending:
      matched_key = match_show(vid["raw_name"])

      if not matched_key:
        unmatched_list.append(vid)
        continue

      ex_list = existing_shows.get(matched_key, [])
      is_duplicate = any(v["id"] == vid["id"] for v in ex_list)

      if is_duplicate:
        duplicate_count += 1
        continue

      vid_obj = {"id": vid["id"], "raw_name": vid["raw_name"]}
      ex_list.append(vid_obj)
      existing_shows[matched_key] = ex_list
      auto_saved += 1

    if auto_saved > 0:
      if not doc:
        video_col.insert_one({"date": target_date, "shows": existing_shows})
      else:
        video_col.update_one(
            {"date": target_date}, {"$set": {"shows": existing_shows}}
        )

    msg = f"✅ <b>तारीख सेट हो गई:</b> <b>{target_date.title()}</b>\n\n"
    msg += (
        f"🤖 <b>स्वचालित रूप से (Matched) सेव हुए:</b> <b>{auto_saved} शोज़</b>\n"
    )

    if duplicate_count > 0:
      msg += f"⚠️ <b>पहले से मौजूद (Duplicates):</b> <b>{duplicate_count} वीडियोस</b>\n"

    await update.message.reply_text(msg, parse_mode="HTML")

    # 📌 अगर कोई अनमैच शो मिला तो अलग से बटन देकर पूछेगा
    if unmatched_list:
      await update.message.reply_text(
          f"⚠️ <b>{len(unmatched_list)} शोज़ मैच नहीं हो पाए!</b>\n"
          "नीचे दिए गए शोज़ के लिए बटन बनाने हेतु क्लिक करें:",
          parse_mode="HTML",
      )

      for idx, u_vid in enumerate(unmatched_list):
        auto_suggested = extract_show_title_auto(u_vid["raw_name"])
        det_ott = detect_ott_tag(u_vid["raw_name"])

        btn = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "➕ Add Show & Button",
                callback_data=f"addmanual_{target_date}_{det_ott}_{idx}",
            )
        ]])

        # टेंपरेरी स्टोर ताकि क्लिक करने पर नाम माँग सके
        context.user_data[f"unmatch_{idx}"] = u_vid

        await update.message.reply_text(
            f"❓ <b>Unmatched Show #{idx+1}:</b>\n"
            f"📄 <b>File Name:</b> <code>{u_vid['raw_name']}</code>\n"
            f"💡 <b>Suggested Title:</b> {auto_suggested}\n"
            f"📺 <b>Detected OTT:</b> {det_ott.split('_')[0].upper()}",
            reply_markup=btn,
            parse_mode="HTML",
        )
    return

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
    context.user_data["selected_date"] = text.lower()
    buttons = [
        [InlineKeyboardButton("SunNXT", callback_data="sunnxt_p1")],
        [InlineKeyboardButton("Zee5", callback_data="zee5_p1")],
        [InlineKeyboardButton("DangalPlay", callback_data="dangal_p1")],
        [
            InlineKeyboardButton(
                "Hotstar(StarPlus & Colors)", callback_data="hotstar_p1"
            )
        ],
        [InlineKeyboardButton("SonyLiv", callback_data="sonyliv_p1")],
        [InlineKeyboardButton("❌ Close", callback_data="close")],
    ]
    await update.message.reply_text(
        "✅ <b>Data fetched successfully!</b>\n\n"
        f"📅 <b>Date Requested:</b>\n<b>{text.title()}</b>\n\n"
        "🔍 <b>Please choose your desired OTT below:</b>",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML",
    )


async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  await query.answer()

  data = query.data
  user_date = context.user_data.get("selected_date", "")

  if data.startswith("addmanual_"):
    parts = data.split("_")
    t_date = parts[1]
    t_ott = f"{parts[2]}_{parts[3]}"
    idx = parts[4]

    u_vid = context.user_data.get(f"unmatch_{idx}")
    context.user_data["manual_vid"] = u_vid
    context.user_data["manual_date"] = t_date
    context.user_data["manual_ott"] = t_ott
    context.user_data["adding_manual_show"] = True

    await query.message.reply_text(
        f"✍️ <b>कृपया इस शो का सही नाम लिखकर भेजें:</b>\n"
        f"📄 File: <code>{u_vid['raw_name']}</code>\n\n"
        "<i>आपके नाम भेजते ही बॉट इसका ऑटोमैटिक बटन बनाकर ऐड कर देगा!</i>",
        parse_mode="HTML",
    )
    return

  elif data == "close":
    await query.message.delete()
    return

  elif data == "back_ott":
    buttons = [
        [InlineKeyboardButton("SunNXT", callback_data="sunnxt_p1")],
        [InlineKeyboardButton("Zee5", callback_data="zee5_p1")],
        [InlineKeyboardButton("DangalPlay", callback_data="dangal_p1")],
        [
            InlineKeyboardButton(
                "Hotstar(StarPlus & Colors)", callback_data="hotstar_p1"
            )
        ],
        [InlineKeyboardButton("SonyLiv", callback_data="sonyliv_p1")],
        [InlineKeyboardButton("❌ Close", callback_data="close")],
    ]
    disp_date = user_date.title() if user_date else "Selected Date"
    await query.message.edit_text(
        "✅ <b>Data fetched successfully!</b>\n\n"
        f"📅 <b>Date Requested:</b>\n<b>{disp_date}</b>\n\n"
        "🔍 <b>Please choose your desired OTT below:</b>",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML",
    )

  elif data.startswith("ott_") or data.endswith("_p1"):
    all_shows = get_all_shows()

    show_buttons = []
    for key, info in all_shows.items():
      if info["ott"] == data:
        show_buttons.append([
            InlineKeyboardButton(
                f"{info['name']} ↗️", callback_data=f"show_{key}"
            )
        ])

    disp_date = user_date.title() if user_date else "Selected Date"

    if show_buttons:
      show_buttons.append([
          InlineKeyboardButton("⬅️ Choose OTT", callback_data="back_ott"),
          InlineKeyboardButton("❌ Close", callback_data="close"),
      ])
      await query.message.edit_text(
          f"🎬 <b>{data.split('_')[0].upper()} Shows</b>\n\n"
          f"📅 <b>Chosen Date:</b> <b>{disp_date}</b>\n\n"
          "🎯 <b>Choose a Show Below:</b>",
          reply_markup=InlineKeyboardMarkup(show_buttons),
          parse_mode="HTML",
      )

  elif data.startswith("show_"):
    show_key = data.replace("show_", "")
    doc = video_col.find_one({"date": user_date})
    date_db = doc.get("shows", {}) if doc else {}
    video_list = date_db.get(show_key, [])

    if video_list:
      for vid_obj in video_list:
        r_name = vid_obj.get("raw_name", "Episode_Video.DKLRDR.mp4")
        fresh_caption = build_html_caption(r_name)

        await context.bot.send_video(
            chat_id=query.message.chat_id,
            video=vid_obj["id"],
            caption=fresh_caption,
            parse_mode="HTML",
        )

      notice_text = (
          "╭─────── ‼️ <b>Auto-Delete Notice</b> ‼️ ───────╮\n\n"
          "🚨 <b>Make sure to save the video!</b>\n"
          "⏰ <b>Videos Will Be Auto-deleted After 60 minutes to avoid copyright"
          " issue</b> ⌛\n"
          "📬 <b>Forward it to Saved Messages and Watch there</b>\n\n"
          "╰────────────────────────────────────╯"
      )
      await context.bot.send_message(
          chat_id=query.message.chat_id,
          text=notice_text,
          parse_mode="HTML",
      )
    else:
      disp_date = user_date.title() if user_date else "Selected Date"
      await query.message.reply_text(
          f"❌ <b>इस तारीख ({disp_date}) में इस शो की कोई वीडियो उपलब्ध नहीं है!</b>",
          parse_mode="HTML",
      )


# ----------------- BACKGROUND USERBOT RUNNER -----------------
def start_userbot():
  loop = asyncio.new_event_loop()
  asyncio.set_event_loop(loop)
  userbot = Client(
      "dklr_integrated_userbot", api_id=API_ID, api_hash=API_HASH
  )

  @userbot.on_message(
      filters.chat(SOURCE_CHANNELS) & (filters.video | filters.document

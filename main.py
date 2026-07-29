import os
import re
from threading import Thread
from flask import Flask
import pymongo
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ----------------- FLASK SERVER FOR RENDER -----------------
app = Flask(__name__)


@app.route("/")
def home():
  return "DKLR TV Bot is Active with Duplicate Protection!"


def run():
  port = int(os.environ.get("PORT", 8080))
  app.run(host="0.0.0.0", port=port)


def keep_alive():
  t = Thread(target=run)
  t.start()


keep_alive()

# ----------------- CONFIG & MONGODB SETUP -----------------
BOT_TOKEN = "8909033238:AAHiDgwzXyNCRplZ8GTEGvTJJyrGS7kX20o"
MONGO_URI = os.environ.get(
    "MONGO_URI",
    "mongodb+srv://deepakkumar451811_db_user:z0gBb13CSvYAECgG@cluster0.osysn1c.mongodb.net/?appName=Cluster0",
)

client = pymongo.MongoClient(MONGO_URI)
db = client["dklr_bot_db"]
video_col = db["videos"]
shows_col = db["custom_shows"]

# डिफॉल्ट शोज़ डेटाबेस
DEFAULT_SHOWS = {
    "tu_hi_re": {"name": "Tu Hi Re Dil Mein", "ott": "zee5_p1"},
    "lakshmi_nivas": {"name": "Lakshmi Nivas", "ott": "zee5_p1"},
    "tumm_se_tumm": {"name": "Tumm Se Tumm Tak", "ott": "zee5_p1"},
    "ganga_mai": {"name": "Ganga Mai Ki Betiyan", "ott": "zee5_p1"},
    "vasudha": {"name": "Vasudha", "ott": "zee5_p1"},
    "humari_radha": {"name": "Humari Radha", "ott": "zee5_p1"},
    "jagadhatri": {"name": "Jagadhatri", "ott": "zee5_p1"},
    "jaane_anjaane": {"name": "Jaane Anjaane Hum Mile", "ott": "zee5_p1"},
    "greatest_show": {"name": "The Greatest Show on Earth", "ott": "zee5_p1"},
    "pati_anaadi": {"name": "PATI ANAADI", "ott": "dangal_p1"},
    "pati_bhramachari": {"name": "PATI BHRAMACHARI", "ott": "dangal_p1"},
    "mann_atisundar": {"name": "MANN ATISUNDAR", "ott": "dangal_p1"},
    "rimjhim": {"name": "RIMJHIM", "ott": "dangal_p1"},
    "ishq_junooni": {"name": "ISHQ JUNOONI", "ott": "dangal_p1"},
    "tees_ke_paar": {"name": "TEES KE PAAR JAB MILA PYAR", "ott": "dangal_p1"},
    "kaisi_teri": {"name": "KAISI TERI DILLAGI", "ott": "dangal_p1"},
    "mann_sundar": {"name": "MANN SUNDAR", "ott": "dangal_p1"},
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
    "hui_gumm": {
        "name": "Hui Gumm Yaadein Ek Doctor Do Zindagiyaar",
        "ott": "sonyliv_p1",
    },
    "tmkoc": {"name": "Taarak Mehta Ka Ooltah Chashmah", "ott": "sonyliv_p1"},
    "hastinapur": {"name": "Hastinapur Ke Veer", "ott": "sonyliv_p1"},
    "tum_ho_naa": {"name": "Tum Ho Naa - Ghar Ki Superstar", "ott": "sonyliv_p1"},
    "pushpa": {"name": "Pushpa Impossible", "ott": "sonyliv_p1"},
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
  if ".HS." in text or " HS " in text or "HOTSTAR" in text or "HS.WEB" in text:
    return "hotstar_p1"
  elif (
      ".Z5." in text
      or " Z5 " in text
      or "ZEE5" in text
      or ".ZEE." in text
      or "ZEE" in text
  ):
    return "zee5_p1"
  elif ".SL." in text or " SONY " in text or "SONYLIV" in text or ".SL " in text:
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
  clean = raw_name.replace("DKLR_DR", "").replace(".mp4", "").replace("_", " ")
  parts = clean.split(".")
  title_part = parts[0].strip()
  title_part = re.sub(
      r"(Season|Episode|Ep|\d+)", "", title_part, flags=re.IGNORECASE
  ).strip()
  if not title_part or len(title_part) < 3:
    title_part = "Auto Show " + raw_name[:8]
  return title_part.title()


def match_show(caption):
  text = caption.lower().replace(".", " ").replace("_", " ")
  all_shows = get_all_shows()

  key_map = {
      "yrkkh": "yrkkh",
      "yeh rishta": "yrkkh",
      "anupama": "anupama",
      "tmkoc": "tmkoc",
      "taarak": "tmkoc",
      "pushpa": "pushpa",
      "udne ki": "udne_ki_aasha",
      "vasudha": "vasudha",
      "jagadhatri": "jagadhatri",
      "lakshmi": "lakshmi_nivas",
  }

  for k, s_key in key_map.items():
    if k in text:
      return s_key

  for s_key, data in all_shows.items():
    name_clean = data["name"].lower().replace("-", " ")
    words = [w for w in name_clean.split() if len(w) > 3]
    if any(w in text for w in words):
      return s_key

  return None


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if update.message:
    await update.message.reply_text(
        "**नमस्ते भाई! कृपया कोई तारीख लिखकर भेजें (जैसे: 24 July 2026)।**",
        parse_mode="Markdown",
    )


async def handle_video_upload(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
  if update.message and update.message.video:
    file_id = update.message.video.file_id
    raw_name = (
        update.message.caption or update.message.video.file_name or ""
    )
    cleaned_name = raw_name.replace("TvShowHub", "DKLR_DR").replace(
        "tvshowhub", "DKLR_DR"
    )

    if not cleaned_name:
      cleaned_name = "Episode_Video.DKLR_DR.mp4"

    final_caption = (
        f"**{cleaned_name}**\n\n"
        "⚡️**Join :-** [ **@DKLR_DR** ]\n\n"
        "📌 **Join:** https://t.me/+AT1UIPpK3c04MTk1\n\n"
        "📌 **Upcoming New Episode -** https://t.me/+sN83w5txQO9hNTdl"
    )

    if "pending_videos" not in context.user_data:
      context.user_data["pending_videos"] = []

    context.user_data["pending_videos"].append({
        "id": file_id,
        "caption": final_caption,
        "raw_name": cleaned_name,
    })
    context.user_data["awaiting_upload_date"] = True

    total_rec = len(context.user_data["pending_videos"])
    await update.message.reply_text(
        f"🎥 **वीडियो प्राप्त हो गई! (कुल: {total_rec})**\n\n"
        "✍️ **कृपया तारीख लिखकर भेजें (जैसे: 20 July 2026):**",
        parse_mode="Markdown",
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if not update.message or not update.message.text:
    return

  text = update.message.text.strip()

  if context.user_data.get("awaiting_upload_date"):
    target_date = text.lower()
    context.user_data["awaiting_upload_date"] = False

    pending = context.user_data.get("pending_videos", [])
    context.user_data["pending_videos"] = []

    auto_saved = 0
    duplicate_count = 0
    new_auto_shows = []

    doc = video_col.find_one({"date": target_date})
    existing_shows = doc.get("shows", {}) if doc else {}

    for vid in pending:
      matched_key = match_show(vid["raw_name"])

      # अगर नया अनमैच्ड शो है ➔ ऑटो-ऐड
      if not matched_key:
        auto_title = extract_show_title_auto(vid["raw_name"])
        matched_key = auto_title.lower().replace(" ", "_")
        detected_ott = detect_ott_tag(vid["raw_name"])

        shows_col.update_one(
            {"key": matched_key},
            {"$set": {"key": matched_key, "name": auto_title, "ott": detected_ott}},
            upsert=True,
        )

        ott_clean_name = detected_ott.split("_")[0].upper()
        if auto_title not in new_auto_shows:
          new_auto_shows.append(f"• **{auto_title}** *({ott_clean_name})*")

      # 🚫 डुप्लीकेट चेकिंग (अगर यह वीडियो फाइल पहले से इस शो में है तो सेव मत करो)
      ex_list = existing_shows.get(matched_key, [])
      is_duplicate = any(v["id"] == vid["id"] for v in ex_list)

      if is_duplicate:
        duplicate_count += 1
        continue

      vid_obj = {"id": vid["id"], "caption": vid["caption"]}
      ex_list.append(vid_obj)
      existing_shows[matched_key] = ex_list
      auto_saved += 1

    # MongoDB में अपडेट करें
    if auto_saved > 0:
      if not doc:
        video_col.insert_one(
            {"date": target_date, "shows": existing_shows}
        )
      else:
        video_col.update_one(
            {"date": target_date}, {"$set": {"shows": existing_shows}}
        )

    msg = f"✅ **तारीख सेट हो गई:** **{target_date.title()}**\n\n"
    msg += f"🤖 **सफलतापूर्वक नए सेव हुए:** **{auto_saved} वीडियोस**\n"

    if duplicate_count > 0:
      msg += (
          f"⚠️ **डुप्लीकेट (पहले से मौजूद) छोड़ दिए गए:** **{duplicate_count}"
          " वीडियोस**\n"
      )

    if new_auto_shows:
      msg += "\n🆕 **नए शोज़ ऑटो-पहचान कर ऐड किए गए:**\n"
      for ns in new_auto_shows:
        msg += f"{ns}\n"

    msg += "\n🎉 **प्रोसेस पूरी हो गई है!**"
    await update.message.reply_text(msg, parse_mode="Markdown")
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
        "✅ **Data fetched successfully!**\n\n"
        f"📅 **Date Requested:**\n**{text.title()}**\n\n"
        "🔍 **Please choose your desired OTT below:**",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown",
    )


async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  await query.answer()

  data = query.data
  user_date = context.user_data.get("selected_date", "")

  if data == "close":
    await query.message.delete()
    return

  elif data.startswith("ott_") or data.endswith("_p1"):
    all_shows = get_all_shows()
    doc = video_col.find_one({"date": user_date})
    date_db = doc.get("shows", {}) if doc else {}

    show_buttons = []
    for key, info in all_shows.items():
      if info["ott"] == data and key in date_db and len(date_db[key]) > 0:
        show_buttons.append([
            InlineKeyboardButton(
                f"{info['name']} ↗️", callback_data=f"show_{key}"
            )
        ])

    if show_buttons:
      show_buttons.append([
          InlineKeyboardButton("⬅️ Choose OTT", callback_data="back_ott"),
          InlineKeyboardButton("❌ Close", callback_data="close"),
      ])
      await query.message.edit_text(
          f"🎬 **{data.split('_')[0].upper()} Shows**\n\n"
          f"📅 **Chosen Date:** **{user_date.title()}**\n\n"
          "🎯 **Choose a Show Below:**",
          reply_markup=InlineKeyboardMarkup(show_buttons),
          parse_mode="Markdown",
      )
    else:
      await query.message.reply_text(
          "❌ **No data found for that date.**", parse_mode="Markdown"
      )

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
    await query.message.edit_text(
        "✅ **Data fetched successfully!**\n\n"
        f"📅 **Date Requested:**\n**{user_date.title()}**\n\n"
        "🔍 **Please choose your desired OTT below:**",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown",
    )

  elif data.startswith("show_"):
    show_key = data.replace("show_", "")
    doc = video_col.find_one({"date": user_date})
    date_db = doc.get("shows", {}) if doc else {}
    video_list = date_db.get(show_key, [])

    if video_list:
      await query.message.delete()
      for vid_obj in video_list:
        await context.bot.send_video(
            chat_id=query.message.chat_id,
            video=vid_obj["id"],
            caption=vid_obj["caption"],
            parse_mode="Markdown",
        )

      notice_text = (
          "╭─────── ‼️ **Auto-Delete Notice** ‼️ ───────╮\n\n"
          "🚨 **Make sure to save the video!**\n"
          "⏰ **Videos Will Be Auto-deleted After 60 minutes to avoid copyright"
          " issue** ⌛\n"
          "📬 **Forward it to Saved Messages and Watch there**\n\n"
          "╰────────────────────────────────────╯"
      )
      await context.bot.send_message(
          chat_id=query.message.chat_id,
          text=notice_text,
          parse_mode="Markdown",
      )


if __name__ == "__main__":
  tg_app = ApplicationBuilder().token(BOT_TOKEN).build()
  tg_app.add_handler(CommandHandler("start", start_command))
  tg_app.add_handler(MessageHandler(filters.VIDEO, handle_video_upload))
  tg_app.add_handler(
      MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)
  )
  tg_app.add_handler(CallbackQueryHandler(button_click))

  print("Duplicates Filter & Full Auto Active...")
  tg_app.run_polling()

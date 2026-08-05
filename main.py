import asyncio
from datetime import datetime
import io
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

# ----------------- FLASK SERVER FOR RENDER (KEEP-ALIVE) -----------------
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

# ----------------- CONFIG & MONGODB SETUP -----------------
BOT_TOKEN = os.environ.get(
    "BOT_TOKEN", "8658926437:AAHnzF23ypbzIbZ-yATBhA0MHFGVOhVsTzA"
)
MONGO_URI = os.environ.get(
    "MONGO_URI",
    "mongodb+srv://deepakkumar451811_db_user:z0gBb13CSvYAECgG@cluster0.osysn1c.mongodb.net/?appName=Cluster0",
)

API_ID = int(os.environ.get("API_ID", "30366893"))
API_HASH = os.environ.get("API_HASH", "ecb01a29588b13c36c8c373584270ea8")
TARGET_BOT_USERNAME = "@autofiltertsh_bot"
SOURCE_CHANNELS = ["tvshowhubb"]

OWNER_USERNAME = "dklr145"

client = pymongo.MongoClient(MONGO_URI)
db = client["dklr_bot_db"]
video_col = db["videos"]
shows_col = db["custom_shows"]
ott_col = db["custom_otts"]

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

  doc = video_col.find_one({
      "$or": [
          {"date": clean_date},
          {"date": alt_date},
          {"date": {"$regex": f"^{clean_date}$", "$options": "i"}},
          {"date": {"$regex": f"^{alt_date}$", "$options": "i"}},
      ]
  })
  return doc


def extract_ep_num(text):
  match = re.search(r"(?:ep|episode|e)[._\s-]*(\d+)", text, re.IGNORECASE)
  if match:
    return match.group(1)
  return None


def extract_base_title(raw_name):
  clean = (
      raw_name.replace("TvShowHub", "")
      .replace("tvshowhub", "")
      .replace("DKLRShowhub", "")
      .replace("DKLRDR", "")
  )
  clean_text = clean.replace(".", " ").replace("_", " ")

  parts = clean_text.split()
  title_parts = []
  for p in parts:
    if re.search(
        r"^(Season|Episode|Ep|E\d+|\d+p|Web|Dl|AAC|H|264|DangalPlay|Hotstar|Zee5|SonyLiv|SunNXT)",
        p,
        re.IGNORECASE,
    ):
      break
    title_parts.append(p)

  title_part = " ".join(title_parts).strip()
  if not title_part or len(title_part) < 2:
    title_part = "Unmatched Show " + raw_name[:10]
  return title_part.title()


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


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if update.message:
    buttons = [
        [
            InlineKeyboardButton("➕ Add New Show", callback_data="btn_add_show"),
            InlineKeyboardButton("➕ Add New OTT", callback_data="btn_add_ott"),
        ]
    ]
    await update.message.reply_text(
        "<b>नमस्ते भाई! कृपया कोई तारीख लिखकर भेजें (जैसे: 01 August 2026)।</b>\n\n"
        "👇 <b>नया शो या OTT प्लेटफ़ॉर्म जोड़ने के लिए नीचे दिए बटन दबाएँ:</b>",
        reply_markup=InlineKeyboardMarkup(buttons),
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
        "✍️ <b>कृपया तारीख लिखकर भेजें (जैसे: 01 August 2026):</b>",
        parse_mode="HTML",
    )


async def save_manual_show_to_db(
    context, show_name, show_key, ott_tag, target_date, vid_list
):
  shows_col.update_one(
      {"key": show_key},
      {"$set": {"key": show_key, "name": show_name, "ott": ott_tag}},
      upsert=True,
  )

  doc = find_db_doc_by_date(target_date)
  existing_shows = doc.get("shows", {}) if doc else {}

  if show_key not in existing_shows:
    existing_shows[show_key] = []

  for new_v in vid_list:
    new_ep = extract_ep_num(new_v["raw_name"])
    replaced = False

    if new_ep:
      for i, old_v in enumerate(existing_shows[show_key]):
        old_ep = extract_ep_num(old_v["raw_name"])
        if old_ep == new_ep:
          existing_shows[show_key][i] = new_v
          replaced = True
          break

    if not replaced:
      existing_shows[show_key].append(new_v)

  if not doc:
    video_col.insert_one(
        {"date": target_date.lower(), "shows": existing_shows}
    )
  else:
    video_col.update_one({"_id": doc["_id"]}, {"$set": {"shows": existing_shows}})

  display_ott = ott_tag.split("_")[0].upper()
  return (
      f"✅ <b>नया शो सफ़लतापूर्वक ऐडेड!</b>\n\n"
      f"🎬 <b>Show Name:</b> {show_name}\n"
      f"📺 <b>OTT:</b> {display_ott}\n"
      f"📁 <b>Total Files Saved:</b> {len(existing_shows[show_key])} Videos\n"
      f"📅 <b>Date:</b> {target_date.title()}\n\n"
      "🎉 <b>अब ये सभी वीडियोस इस एक शो के बटन में खुलेंगी!</b>"
  )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if not update.message or not update.message.text:
    return

  text = update.message.text.strip()

  # 1. ADD NEW OTT NAME
  if context.user_data.get("adding_new_ott_mode"):
    ott_name = text.strip()
    ott_tag = ott_name.lower().replace(" ", "") + "_p1"

    ott_col.update_one(
        {"tag": ott_tag}, {"$set": {"name": ott_name, "tag": ott_tag}}, upsert=True
    )
    context.user_data["adding_new_ott_mode"] = False
    await update.message.reply_text(
        f"✅ <b>नया OTT प्लेटफ़ॉर्म सफलतापूर्वक जोड़ा गया!</b>\n\n"
        f"📺 <b>OTT Name:</b> {ott_name}\n\n"
        "🎉 <b>अब जब भी इस OTT का शो अपलोड होगा, यह ऑटो-शो होने लगेगा!</b>",
        parse_mode="HTML",
    )
    return

  # 2. ADD NEW SHOW NAME -> CHOOSE OTT
  if context.user_data.get("adding_new_show_step1"):
    show_name = text.strip().title()
    show_key = show_name.lower().replace(" ", "_")
    context.user_data["temp_show_name"] = show_name
    context.user_data["temp_show_key"] = show_key
    context.user_data["adding_new_show_step1"] = False

    all_otts = get_all_otts()
    ott_buttons = []
    for o_name, o_tag in all_otts:
      ott_buttons.append(
          [InlineKeyboardButton(o_name, callback_data=f"save_show_ott|{o_tag}")]
      )

    await update.message.reply_text(
        f"🎬 <b>Show Name:</b> {show_name}\n\n"
        "👇 <b>कृपया इस शो के लिए सही OTT सेलेक्ट करें:</b>",
        reply_markup=InlineKeyboardMarkup(ott_buttons),
        parse_mode="HTML",
    )
    return

  # 3. MANUAL UNMATCHED SHOW NAME -> AUTO-DETECT OTT OR ASK
  if context.user_data.get("adding_manual_show"):
    show_name = text.title()
    show_key = show_name.lower().replace(" ", "_")
    target_date = context.user_data.get("manual_date")
    vid_list = context.user_data.get("manual_vid_list", [])

    context.user_data["adding_manual_show"] = False

    auto_detected_ott = None
    if vid_list:
      auto_detected_ott = detect_ott_tag(vid_list[0].get("raw_name", ""))

    if auto_detected_ott:
      res_msg = await save_manual_show_to_db(
          context,
          show_name,
          show_key,
          auto_detected_ott,
          target_date,
          vid_list,
      )
      await update.message.reply_text(res_msg, parse_mode="HTML")
    else:
      context.user_data["temp_m_show_name"] = show_name
      context.user_data["temp_m_show_key"] = show_key

      all_otts = get_all_otts()
      ott_buttons = []
      for o_name, o_tag in all_otts:
        ott_buttons.append([
            InlineKeyboardButton(
                f"📺 {o_name}", callback_data=f"confirm_m_ott|{o_tag}"
            )
        ])

      await update.message.reply_text(
          f"🎬 <b>Show Name:</b> {show_name}\n\n"
          "👇 <b>कृपया इस शो के लिए OTT प्लेटफ़ॉर्म चुनें:</b>",
          reply_markup=InlineKeyboardMarkup(ott_buttons),
          parse_mode="HTML",
      )
    return

  # 4. DATE ENTRY AFTER UPLOAD (GROUP UNMATCHED BY SHOW TITLE)
  if context.user_data.get("awaiting_upload_date"):
    target_date = text.lower().strip()
    context.user_data["awaiting_upload_date"] = False

    pending = context.user_data.get("pending_videos", [])
    context.user_data["pending_videos"] = []

    auto_saved = 0
    replaced_count = 0
    unmatched_list = []

    doc = find_db_doc_by_date(target_date)
    existing_shows = doc.get("shows", {}) if doc else {}

    for vid in pending:
      matched_key = match_show(vid["raw_name"])
      if not matched_key:
        unmatched_list.append(vid)
        continue

      if matched_key not in existing_shows:
        existing_shows[matched_key] = []

      new_ep = extract_ep_num(vid["raw_name"])
      is_replaced = False

      if new_ep:
        for idx, old_vid in enumerate(existing_shows[matched_key]):
          old_ep = extract_ep_num(old_vid["raw_name"])
          if old_ep == new_ep:
            existing_shows[matched_key][idx] = vid
            replaced_count += 1
            is_replaced = True
            break

      if not is_replaced:
        existing_shows[matched_key].append(vid)

      auto_saved += 1

    if not doc:
      video_col.insert_one({"date": target_date, "shows": existing_shows})
    else:
      video_col.update_one(
          {"_id": doc["_id"]},
          {"$set": {"date": target_date, "shows": existing_shows}},
      )

    msg = f"✅ <b>तारीख सेट हो गई:</b> <b>{target_date.title()}</b>\n\n"
    msg += (
        f"🤖 <b>सफलतापूर्वक प्रोसेस हुए:</b> <b>{auto_saved} वीडियोस</b>\n"
    )

    if replaced_count > 0:
      msg += (
          f"🔄 <b>सेम एपिसोड होने के कारण रिप्लेस किए गए:</b>"
          f" <b>{replaced_count} वीडियोस</b>\n"
      )

    await update.message.reply_text(msg, parse_mode="HTML")

    if unmatched_list:
      clean_date_tag = target_date.replace(" ", "_")

      # GROUP UNMATCHED FILES BY THEIR DETECTED SHOW NAME
      grouped_unmatched = {}
      for u_vid in unmatched_list:
        base_title = extract_base_title(u_vid["raw_name"])
        if base_title not in grouped_unmatched:
          grouped_unmatched[base_title] = []
        grouped_unmatched[base_title].append(u_vid)

      context.user_data["unmatched_groups"] = grouped_unmatched

      buttons = []
      g_idx = 0
      unmatch_info = (
          f"🚨 <b>कुल {len(unmatched_list)} अनमैच फाइल्स मिले हैं!</b>\n\n"
      )

      for g_title, g_vids in grouped_unmatched.items():
        g_idx += 1
        unmatch_info += (
            f"🎬 <b>Show #{g_idx}: {g_title}</b> ({len(g_vids)} Files)\n"
        )
        buttons.append([
            InlineKeyboardButton(
                f"➕ Add '{g_title[:20]}' ({len(g_vids)} Files)",
                callback_data=f"addgroup|{clean_date_tag}|{g_idx-1}",
            )
        ])

      unmatch_info += (
          "\n👇 <b>अलग-अलग शो को जोड़ने के लिए ऊपर दिए संबंधित बटन दबाएँ:</b>"
      )

      await update.message.reply_text(
          unmatch_info,
          reply_markup=InlineKeyboardMarkup(buttons),
          parse_mode="HTML",
      )
    return

  # 5. USER SEARCHING DATE
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
      await update.message.reply_text(
          "🚫 <b>Sorry! You cannot watch today's episode here.</b>\n"
          "👉 <b>Please go to our Main Channel and watch today's episode from"
          " there.</b>\n\n"
          "🚫 <b>माफ़ कीजिए! आप आज की एपिसोड यहां नहीं देख सकते।</b>\n"
          "👉 <b>कृपया हमारे मुख्य चैनल पर जाएं और आज की एपिसोड वहां"
          " देखें।</b>",
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
    buttons = []
    for o_name, o_tag in all_otts:
      if o_tag in uploaded_ott_tags:
        buttons.append([InlineKeyboardButton(o_name, callback_data=f"o|{o_tag}")])

    if buttons:
      buttons.append([InlineKeyboardButton("❌ Close", callback_data="close")])
      await update.message.reply_text(
          "✅ <b>Data fetched successfully!</b>\n\n"
          f"📅 <b>Date Requested:</b>\n<b>{text.title()}</b>\n\n"
          "🔍 <b>Please choose your desired OTT below:</b>",
          reply_markup=InlineKeyboardMarkup(buttons),
          parse_mode="HTML",
      )
    else:
      await update.message.reply_text(
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

  elif data == "btn_add_show":
    context.user_data["adding_new_show_step1"] = True
    await query.message.reply_text(
        "✍️ <b>कृपया नए शो का नाम लिखकर भेजें:</b>", parse_mode="HTML"
    )
    return

  elif data == "btn_add_ott":
    context.user_data["adding_new_ott_mode"] = True
    await query.message.reply_text(
        "✍️ <b>कृपया नए OTT प्लेटफ़ॉर्म का नाम लिखकर भेजें (जैसे: ShemarooMe /"
        " JioCinema):</b>",
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
        f"✅ <b>नया शो सफलतापूर्वक डेटाबेस में जोड़ा गया!</b>\n\n"
        f"🎬 <b>Show Name:</b> {show_name}\n"
        f"📺 <b>OTT Tag:</b> {ott_tag.split('_')[0].upper()}\n\n"
        "🎉 <b>अब जब भी इस नाम का शो आएगा, बॉट इसे ऑटो-मैच कर लेगा!</b>",
        parse_mode="HTML",
    )
    return

  elif data.startswith("confirm_m_ott|"):
    ott_tag = data.split("|")[1]
    show_name = context.user_data.get("temp_m_show_name")
    show_key = context.user_data.get("temp_m_show_key")
    target_date = context.user_data.get("manual_date")
    vid_list = context.user_data.get("manual_vid_list", [])

    res_msg = await save_manual_show_to_db(
        context, show_name, show_key, ott_tag, target_date, vid_list
    )
    await query.message.reply_text(res_msg, parse_mode="HTML")
    return

  elif data.startswith("addgroup|"):
    _, clean_date_tag, group_idx_str = data.split("|")
    target_date = clean_date_tag.replace("_", " ")
    g_idx = int(group_idx_str)

    grouped_unmatched = context.user_data.get("unmatched_groups", {})
    titles_list = list(grouped_unmatched.keys())

    if g_idx < len(titles_list):
      selected_title = titles_list[g_idx]
      selected_vids = grouped_unmatched[selected_title]

      context.user_data["manual_vid_list"] = selected_vids
      context.user_data["manual_date"] = target_date
      context.user_data["adding_manual_show"] = True

      await query.message.reply_text(
          f"✍️ <b>कृपया इस शो ({selected_title}) का सही नाम पढ़कर लिखकर भेजें:</b>\n\n"
          f"<i>कुल {len(selected_vids)} फाइल्स इस शो में सेव होंगी।</i>",
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
          f"🎬 <b>{ott_tag.split('_')[0].upper()} Shows</b>\n\n"
          f"📅 <b>Chosen Date:</b> <b>{disp_date}</b>\n\n"
          "🎯 <b>Available Shows Below:</b>",
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
    buttons = []
    for o_name, o_tag in all_otts:
      if o_tag in uploaded_ott_tags:
        buttons.append([InlineKeyboardButton(o_name, callback_data=f"o|{o_tag}")])
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


# ----------------- BACKGROUND USERBOT RUNNER -----------------
async def start_userbot():
  userbot = Client(
      "dklr_integrated_userbot",
      api_id=API_ID,
      api_hash=API_HASH,
      in_memory=True,
  )

  @userbot.on_message(
      filters.chat(SOURCE_CHANNELS) & (filters.video | filters.document)
  )
  async def forward_video(client, message):
    try:
      await message.forward(TARGET_BOT_USERNAME)
      print("✅ [UserBot] Auto-forwarded video successfully!")
    except Exception as e:
      print(f"❌ [UserBot Error]: {e}")

  try:
    print("🚀 [UserBot] Starting Engine...")
    await userbot.start()
    print("✅ [UserBot] Active & Listening!")
  except Exception as e:
    print(f"⚠️ UserBot Exception: {e}")


def main():
  loop = asyncio.new_event_loop()
  asyncio.set_event_loop(loop)

  loop.create_task(start_userbot())

  tg_app = ApplicationBuilder().token(BOT_TOKEN).build()
  tg_app.add_handler(CommandHandler("start", start_command))
  tg_app.add_handler(MessageHandler(tg_filters.VIDEO, handle_video_upload))
  tg_app.add_handler(
      MessageHandler(tg_filters.TEXT & ~tg_filters.COMMAND, handle_text)
  )
  tg_app.add_handler(CallbackQueryHandler(button_click))

  print("DKLR Show Hub Bot Engine Live...")
  tg_app.run_polling(close_loop=False)


if __name__ == "__main__":
  main()

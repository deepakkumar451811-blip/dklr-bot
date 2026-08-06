import os
import re
from threading import Thread
from flask import Flask
from pyrogram import Client, filters

# ----------------- FLASK KEEP-ALIVE -----------------
app = Flask(__name__)


@app.route("/")
def home():
  return "DKLR Userbot Active!"


def run_flask():
  port = int(os.environ.get("PORT", 8080))
  app.run(host="0.0.0.0", port=port)


Thread(target=run_flask).start()

# ----------------- USERBOT CONFIG -----------------
API_ID = int(os.environ.get("API_ID", "30366893"))
API_HASH = os.environ.get("API_HASH", "ecb01a29588b13c36c8c373584270ea8")
STRING_SESSION = os.environ.get("STRING_SESSION", "")

SOURCE_CHAT = os.environ.get("SOURCE_CHAT", "")
TARGET_CHAT = os.environ.get("TARGET_CHAT", "@DKLRShowhub")

userbot = Client(
    "dklr_userbot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=STRING_SESSION,
)


def build_dklr_caption_and_name(raw_name):
  base_name = re.sub(
      r"\.(mp4|mkv|avi|mov|webm|flv)$", "", raw_name, flags=re.IGNORECASE
  )
  base_name = re.sub(
      r"[-_.\s]+(TvShowHub|ANTONi|webdlbot|DG_Contents|DG_Content|UtsavTV|Nx-DRM-DL|DS_Ottwebdlbot|kairax007|ottwebdlbot|DKLR_DR|DKLRDR|DKLRShowhub)[-_.\s]*$",
      "",
      base_name,
      flags=re.IGNORECASE,
  )
  base_name = base_name.strip(".-_ ")
  final_filename = f"{base_name}.DKLRShowhub.mp4"

  caption_text = (
      f"📄 <b>{final_filename}</b>\n\n"
      "⚡️ <b>Join :-</b> [ <b>@DKLRShowhub</b> ]\n\n"
      '📌 <b>Join:</b> <a'
      ' href="https://t.me/+AT1UIPpK3c04MTk1">https://t.me/+AT1UIPpK3c04MTk1</a>\n\n'
      '📌 <b>Upcoming New Episode -</b> <a'
      ' href="https://t.me/+sN83w5txQO9hNTdl">https://t.me/+sN83w5txQO9hNTdl</a>'
  )
  return caption_text


@userbot.on_message(filters.chat(SOURCE_CHAT))
async def auto_forward_and_rename(client, message):
  try:
    if message.media:
      file_obj = message.video or message.document
      raw_name = (
          message.caption
          or (file_obj.file_name if file_obj else None)
          or "Episode_Video.mp4"
      )

      caption_text = build_dklr_caption_and_name(raw_name)

      await client.send_cached_media(
          chat_id=TARGET_CHAT,
          file_id=file_obj.file_id,
          caption=caption_text,
          parse_mode="html",
      )
      print(f"Post successfully copied to {TARGET_CHAT}")

    elif message.text:
      await client.send_message(
          chat_id=TARGET_CHAT, text=message.text, parse_mode="html"
      )

  except Exception as e:
    print(f"Error copying post: {e}")


if __name__ == "__main__":
  print("Pyrogram Userbot Engine Started...")
  userbot.run()

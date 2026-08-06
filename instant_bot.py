import os
import re
import telebot

# ----------------- CONFIG & NEW BOT TOKEN -----------------
BOT_TOKEN = os.environ.get(
    "BOT_TOKEN", "8909033238:AAEJAlM_zoHpgVzbBrMEB4zDiCYr4NUBZjo"
)

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")


def build_dklr_caption_and_name(raw_name):
  # 1. Clean file extension from the end
  base_name = re.sub(
      r"\.(mp4|mkv|avi|mov|webm|flv)$", "", raw_name, flags=re.IGNORECASE
  )

  # 2. Clean existing tags, channels or webdl terms
  base_name = re.sub(
      r"[-_.\s]+(TvShowHub|ANTONi|webdlbot|DG_Contents|DG_Content|UtsavTV|Nx-DRM-DL|DS_Ottwebdlbot|kairax007|ottwebdlbot|DKLR_DR|DKLRDR|DKLRShowhub)[-_.\s]*$",
      "",
      base_name,
      flags=re.IGNORECASE,
  )

  base_name = base_name.strip(".-_ ")

  # 3. Attach exact '.DKLRShowhub.mp4' to the very end
  final_filename = f"{base_name}.DKLRShowhub.mp4"

  # 4. Your exact requested HTML Caption
  caption_text = (
      f"📄 <b>{final_filename}</b>\n\n"
      "⚡️ <b>Join :-</b> [ <b>@DKLRShowhub</b> ]\n\n"
      '📌 <b>Join:</b> <a'
      ' href="https://t.me/+AT1UIPpK3c04MTk1">https://t.me/+AT1UIPpK3c04MTk1</a>\n\n'
      '📌 <b>Upcoming New Episode -</b> <a'
      ' href="https://t.me/+sN83w5txQO9hNTdl">https://t.me/+sN83w5txQO9hNTdl</a>'
  )
  return caption_text


@bot.message_handler(commands=["start"])
def start_command(message):
  bot.reply_to(
      message,
      "🚀 <b>DKLR Instant Auto-Rename Bot Active!</b>\n\n"
      "<i>मुझे कोई भी वीडियो या डॉक्यूमेंट भेजें, मैं तुरंत उस पर आपका DKLR नाम"
      " और कैप्शन लगा दूँगा।</i>",
  )


@bot.message_handler(content_types=["video", "document"])
def auto_process_media(message):
  file_obj = message.video or message.document
  if not file_obj:
    return

  raw_name = (
      message.caption
      or getattr(file_obj, "file_name", None)
      or "Episode_Video.mp4"
  )
  caption_text = build_dklr_caption_and_name(raw_name)

  bot.send_document(
      message.chat.id, file_obj.file_id, caption=caption_text, parse_mode="HTML"
  )


if __name__ == "__main__":
  print("Instant Auto-Rename Bot Live...")
  bot.infinity_polling(timeout=10, long_polling_timeout=5)

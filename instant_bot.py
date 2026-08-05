import os
import re
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

BOT_TOKEN = os.environ.get(
    "BOT_TOKEN", "8909033238:AAEJAlM_zoHpgVzbBrMEB4zDiCYr4NUBZjo"
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


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if update.message:
    await update.message.reply_text(
        "🚀 <b>DKLR Instant Auto-Rename Bot Active!</b>\n\n"
        "<i>मुझे कोई भी वीडियो या डॉक्यूमेंट भेजें, मैं तुरंत उस पर आपका DKLR नाम और कैप्शन लगा दूँगा।</i>",
        parse_mode="HTML",
    )


async def auto_process_media(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
  msg = update.message
  file_obj = msg.video or msg.document
  if not file_obj:
    return

  raw_name = msg.caption or file_obj.file_name or "Episode_Video.mp4"
  caption_text = build_dklr_caption_and_name(raw_name)

  await context.bot.send_document(
      chat_id=msg.chat_id,
      document=file_obj.file_id,
      caption=caption_text,
      parse_mode="HTML",
  )


def main():
  app = ApplicationBuilder().token(BOT_TOKEN).build()
  app.add_handler(CommandHandler("start", start_command))
  app.add_handler(
      MessageHandler(filters.VIDEO | filters.DOCUMENT, auto_process_media)
  )
  print("Instant Auto-Rename Bot Engine Live...")
  app.run_polling()


if __name__ == "__main__":
  main()

import asyncio
import os
from pyrogram import Client, filters

# ----------------- CONFIGURATION -----------------
# टेलीग्राम से मिली API डिटेल्स
API_ID = int(os.environ.get("API_ID", "30366893"))
API_HASH = os.environ.get("API_HASH", "ecb01a29588b13c36c8c373584270ea8")

# आपके बॉट का यूज़रनेम (जहाँ वीडियो भेजनी है)
TARGET_BOT_USERNAME = "@DKLR_TV_SHOW_BOT"  # 👈 अपने बॉट का सही यूजरनेम चेक कर लें

# जिन चैनल्स/ग्रुप्स से वीडियोस फॉरवर्ड करनी हैं (ID या Username)
SOURCE_CHANNELS = ["tvshowhubb"]  # 👈 यहाँ उस चैनल का यूज़रनेम या ID डालें

# ----------------- USERBOT CLIENT -----------------
app = Client("dklr_userbot", api_id=API_ID, api_hash=API_HASH)


@app.on_message(
    filters.chat(SOURCE_CHANNELS) & (filters.video | filters.document)
)
async def auto_forward_videos(client, message):
  try:
    print(f"🎥 नई वीडियो मिली: {message.chat.title or message.chat.id}")

    # वीडियो को सीधे आपके मुख्य बॉट में फॉरवर्ड करना
    await message.forward(TARGET_BOT_USERNAME)
    print("✅ वीडियो आपके DKLR बॉट को सफलतापूर्वक भेज दी गई!")

  except Exception as e:
    print(f"❌ फॉरवर्ड करने में एरर: {e}")


if __name__ == "__main__":
  print("🚀 Auto-Forwarder UserBot एक्टिव हो गया है...")
  app.run()

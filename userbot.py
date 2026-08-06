import os
import re
from threading import Thread
from flask import Flask
from pyrogram import Client, filters

# ----------------- FLASK KEEP-ALIVE -----------------
app = Flask(__name__)


@app.route('/')
def home():
  return 'DKLR Smart Userbot Active!'


def run_flask():
  port = int(os.environ.get('PORT', 8080))
  app.run(host='0.0.0.0', port=port)


Thread(target=run_flask).start()

# ----------------- CONFIG VARIABLES -----------------
API_ID = int(os.environ.get('API_ID', '30366893'))
API_HASH = os.environ.get('API_HASH', 'ecb01a29588b13c36c8c373584270ea8')
STRING_SESSION = os.environ.get('STRING_SESSION', '')

userbot = Client(
    'dklr_userbot',
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=STRING_SESSION,
)

# चैनल्स की ID याद रखने के लिए ग्लोबल वेरिएबल
config = {'source_chat': None, 'target_chat': None, 'mode': None}


def build_dklr_caption_and_name(raw_name):
  base_name = re.sub(
      r'\.(mp4|mkv|avi|mov|webm|flv)$', '', raw_name, flags=re.IGNORECASE
  )
  base_name = re.sub(
      r'[-_.\s]+(TvShowHub|ANTONi|webdlbot|DG_Contents|DG_Content|UtsavTV|Nx-DRM-DL|DS_Ottwebdlbot|kairax007|ottwebdlbot|DKLR_DR|DKLRDR|DKLRShowhub)[-_.\s]*$',
      '',
      base_name,
      flags=re.IGNORECASE,
  )
  base_name = base_name.strip('.-_ ')
  final_filename = f'{base_name}.DKLRShowhub.mp4'

  caption_text = (
      f'📄 <b>{final_filename}</b>\n\n'
      '⚡️ <b>Join :-</b> [ <b>@DKLRShowhub</b> ]\n\n'
      '📌 <b>Join:</b> <a'
      ' href="https://t.me/+AT1UIPpK3c04MTk1">https://t.me/+AT1UIPpK3c04MTk1</a>\n\n'
      '📌 <b>Upcoming New Episode -</b> <a'
      ' href="https://t.me/+sN83w5txQO9hNTdl">https://t.me/+sN83w5txQO9hNTdl</a>'
  )
  return caption_text


# ----------------- COMMANDS & SETUP -----------------
@userbot.on_message(filters.me & filters.command('set_source'))
async def set_source_cmd(client, message):
  config['mode'] = 'awaiting_source'
  await message.reply_text(
      '📥 <b>Source Channel सेट करने के लिए:</b>\nअब उस चैनल की कोई भी पोस्ट'
      ' यहाँ <b>Forward</b> करें!'
  )


@userbot.on_message(filters.me & filters.command('set_target'))
async def set_target_cmd(client, message):
  config['mode'] = 'awaiting_target'
  await message.reply_text(
      '📤 <b>Target Channel सेट करने के लिए:</b>\nअब अपने मेन चैनल की कोई भी'
      ' पोस्ट यहाँ <b>Forward</b> करें!'
  )


@userbot.on_message(filters.me & filters.command('status'))
async def status_cmd(client, message):
  src = config['source_chat'] or 'Not Set'
  tgt = config['target_chat'] or 'Not Set'
  await message.reply_text(
      f'📊 <b>Current Config:</b>\n\n📥 <b>Source Channel:</b> {src}\n📤'
      f' <b>Target Channel:</b> {tgt}'
  )


# ----------------- CAPTURE FORWARDED MESSAGES FOR CONFIG -----------------
@userbot.on_message(filters.me & filters.forwarded)
async def capture_forwarded_chats(client, message):
  if config['mode'] == 'awaiting_source':
    if message.forward_from_chat:
      config['source_chat'] = message.forward_from_chat.id
      config['mode'] = None
      await message.reply_text(
          '✅ <b>Source Channel सफलतापूर्वक सेट हो गया!</b>\nChat ID:'
          f' {config["source_chat"]}'
      )
    else:
      await message.reply_text(
          '⚠️ कृपया चैनल का मैसेज ही फ़ॉरवर्ड करें (User/Group का नहीं)।'
      )

  elif config['mode'] == 'awaiting_target':
    if message.forward_from_chat:
      config['target_chat'] = message.forward_from_chat.id
      config['mode'] = None
      await message.reply_text(
          '✅ <b>Target Channel सफलतापूर्वक सेट हो गया!</b>\nChat ID:'
          f' {config["target_chat"]}'
      )
    else:
      await message.reply_text(
          '⚠️ कृपया अपने चैनल का मैसेज फ़ॉरवर्ड करें।'
      )


# ----------------- AUTOMATIC AUTO-FORWARD & RENAME -----------------
@userbot.on_message()
async def auto_forward_logic(client, message):
  # अगर मैसेज उसी Source Channel से आया है जिसे सेट किया गया है
  if config['source_chat'] and message.chat.id == config['source_chat']:
    target = config['target_chat']
    if not target:
      return

    try:
      if message.media:
        file_obj = message.video or message.document
        raw_name = (
            message.caption
            or (file_obj.file_name if file_obj else None)
            or 'Episode_Video.mp4'
        )

        caption_text = build_dklr_caption_and_name(raw_name)

        await client.send_cached_media(
            chat_id=target,
            file_id=file_obj.file_id,
            caption=caption_text,
            parse_mode='html',
        )
        print('Post successfully copied and sent to target!')

      elif message.text:
        await client.send_message(
            chat_id=target, text=message.text, parse_mode='html'
        )

    except Exception as e:
      print(f'Error forwarding: {e}')


if __name__ == '__main__':
  print('Smart Userbot Starting...')
  userbot.run()

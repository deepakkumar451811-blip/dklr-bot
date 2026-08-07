import asyncio
import os
import re
from threading import Thread
from flask import Flask
from telethon import Telethon, events
from telethon.sessions import StringSession

# ----------------- FLASK KEEP-ALIVE -----------------
app = Flask(__name__)


@app.route('/')
def home():
  return 'DKLR Userbot Active!'


def run_flask():
  port = int(os.environ.get('PORT', 8080))
  app.run(host='0.0.0.0', port=port)


Thread(target=run_flask, daemon=True).start()

# ----------------- CONFIG -----------------
API_ID = int(os.environ.get('API_ID', '30366893'))
API_HASH = os.environ.get('API_HASH', 'ecb01a29588b13c36c8c373584270ea8')
STRING_SESSION = os.environ.get('STRING_SESSION', '')

client = Telethon(
    StringSession(STRING_SESSION), API_ID, API_HASH, sequential_updates=True
)

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


# ----------------- COMMANDS -----------------
@client.on(events.NewMessage(outgoing=True, pattern=r'/set_source'))
async def set_source_cmd(event):
  config['mode'] = 'awaiting_source'
  await event.reply(
      '📥 <b>Source Channel सेट करने के लिए:</b>\nअब उस चैनल की कोई भी पोस्ट'
      ' यहाँ <b>Forward</b> करें!',
      parse_mode='html',
  )


@client.on(events.NewMessage(outgoing=True, pattern=r'/set_target'))
async def set_target_cmd(event):
  config['mode'] = 'awaiting_target'
  await event.reply(
      '📤 <b>Target Channel सेट करने के लिए:</b>\nअब अपने मेन चैनल की कोई भी'
      ' पोस्ट यहाँ <b>Forward</b> करें!',
      parse_mode='html',
  )


@client.on(events.NewMessage(outgoing=True, pattern=r'/status'))
async def status_cmd(event):
  src = config['source_chat'] or 'Not Set'
  tgt = config['target_chat'] or 'Not Set'
  await event.reply(
      f'📊 <b>Current Config:</b>\n\n📥 <b>Source Channel:</b> {src}\n📤'
      f' <b>Target Channel:</b> {tgt}',
      parse_mode='html',
  )


# ----------------- FORWARD CAPTURE -----------------
@client.on(events.NewMessage(outgoing=True))
async def capture_forwarded_chats(event):
  if event.fwd_from and event.fwd_from.from_id:
    forwarded_chat = event.fwd_from.from_id
    chat_id = getattr(forwarded_chat, 'channel_id', None)

    if chat_id:
      full_chat_id = int(f'-100{chat_id}')
      if config['mode'] == 'awaiting_source':
        config['source_chat'] = full_chat_id
        config['mode'] = None
        await event.reply(
            f'✅ <b>Source Channel सेट हो गया!</b>\nChat ID: {full_chat_id}',
            parse_mode='html',
        )

      elif config['mode'] == 'awaiting_target':
        config['target_chat'] = full_chat_id
        config['mode'] = None
        await event.reply(
            f'✅ <b>Target Channel सेट हो गया!</b>\nChat ID: {full_chat_id}',
            parse_mode='html',
        )


# ----------------- AUTO FORWARD LOGIC -----------------
@client.on(events.NewMessage)
async def auto_forward_logic(event):
  if config['source_chat'] and event.chat_id == config['source_chat']:
    target = config['target_chat']
    if not target:
      return

    try:
      if event.media:
        raw_name = (
            event.text or getattr(event.media, 'document', None) or 'Episode.mp4'
        )
        if hasattr(raw_name, 'attributes'):
          for attr in raw_name.attributes:
            if hasattr(attr, 'file_name'):
              raw_name = attr.file_name
              break
        if not isinstance(raw_name, str):
          raw_name = 'Episode_Video.mp4'

        caption_text = build_dklr_caption_and_name(raw_name)
        await client.send_file(
            target, event.media, caption=caption_text, parse_mode='html'
        )
      elif event.text:
        await client.send_message(target, event.text, parse_mode='html')
    except Exception as e:
      print(f'Error forwarding: {e}')


async def main():
  await client.start()
  print('Userbot Successfully Started with Telethon!')
  await client.run_until_disconnected()


if __name__ == '__main__':
  loop = asyncio.get_event_loop()
  loop.run_until_complete(main())

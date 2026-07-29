import re
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

BOT_TOKEN = "8909033238:AAHiDgwzXyNCRplZ8GTEGvTJJyrGS7kX20o"

VIDEO_DATABASE = {}

SHOW_NAME_MAP = {
    'tu_hi_re': 'Tu Hi Re Dil Mein',
    'lakshmi_nivas': 'Lakshmi Nivas',
    'tumm_se_tumm': 'Tumm Se Tumm Tak',
    'ganga_mai': 'Ganga Mai Ki Betiyan',
    'vasudha': 'Vasudha',
    'humari_radha': 'Humari Radha',
    'jagadhatri': 'Jagadhatri',
    'jaane_anjaane': 'Jaane Anjaane Hum Mile',
    'greatest_show': 'The Greatest Show on Earth',
    'pati_anaadi': 'PATI ANAADI',
    'pati_bhramachari': 'PATI BHRAMACHARI',
    'mann_atisundar': 'MANN ATISUNDAR',
    'rimjhim': 'RIMJHIM',
    'ishq_junooni': 'ISHQ JUNOONI',
    'tees_ke_paar': 'TEES KE PAAR JAB MILA PYAR',
    'kaisi_teri': 'KAISI TERI DILLAGI',
    'mann_sundar': 'MANN SUNDAR',
    'oh_humnava': 'Oh Humnava - Tum Dena Saath Mera',
    'bareilly': 'Bareilly Ke Bacchan',
    'juliet': 'Tuu Juliet Jatt Di',
    'mahadev': 'Mahadev & Sons',
    'juhi_mui': 'Juhi Mui',
    'do_duniya': 'Do Duniya Ek Dil',
    'parshuram': 'Mr and Mrs Parshuram',
    'anupama': 'Anupama',
    'yrkkh': 'Yeh Rishta Kya Kehlata Hai',
    'sairaab': 'Sairaab',
    'mannat': 'Mannat - Har Khushi Paane Ki',
    'seher': 'Seher Hone Ko Hai',
    'aarambhi': 'Dr Aarambhi',
    'udne_ki_aasha': 'Udne Ki Aasha',
    'kyunki_saas': 'Kyunki Saas Bhi Kabhi Bahu Thi',
    'kyunki_rishton': 'Kyunki Rishton Ke Bhi Roop Badalte Hain',
    'hui_gumm': 'Hui Gumm Yaadein Ek Doctor Do Zindagiyaar',
    'tmkoc': 'Taarak Mehta Ka Ooltah Chashmah',
    'hastinapur': 'Hastinapur Ke Veer',
    'tum_ho_naa': 'Tum Ho Naa - Ghar Ki Superstar',
    'pushpa': 'Pushpa Impossible',
    'thodi_si_umeed': 'Thodi Si Umeed Thoda Sa Aasman',
    'divya_prem': 'Divya Prem'
}

OTT_SHOWS_MAP = {
    "zee5_p1": ['tu_hi_re', 'lakshmi_nivas', 'tumm_se_tumm', 'ganga_mai', 'vasudha', 'humari_radha', 'jagadhatri', 'jaane_anjaane', 'greatest_show'],
    "dangal_p1": ['pati_anaadi', 'pati_bhramachari', 'mann_atisundar', 'rimjhim', 'ishq_junooni', 'tees_ke_paar', 'kaisi_teri', 'mann_sundar'],
    "hotstar_p1": ['oh_humnava', 'bareilly', 'juliet', 'mahadev', 'juhi_mui', 'do_duniya', 'parshuram', 'anupama', 'yrkkh', 'sairaab', 'mannat', 'seher', 'aarambhi', 'udne_ki_aasha', 'kyunki_saas', 'kyunki_rishton'],
    "sonyliv_p1": ['hui_gumm', 'tmkoc', 'hastinapur', 'tum_ho_naa', 'pushpa'],
    "sunnxt_p1": ['thodi_si_umeed', 'divya_prem']
}

UPLOAD_SHOWS = {
    "up_zee5": [
        [InlineKeyboardButton("Tu Hi Re Dil Mein", callback_data='save_tu_hi_re')],
        [InlineKeyboardButton("Lakshmi Nivas", callback_data='save_lakshmi_nivas')],
        [InlineKeyboardButton("Tumm Se Tumm Tak", callback_data='save_tumm_se_tumm')],
        [InlineKeyboardButton("Ganga Mai Ki Betiyan", callback_data='save_ganga_mai')],
        [InlineKeyboardButton("Vasudha", callback_data='save_vasudha')],
        [InlineKeyboardButton("Humari Radha", callback_data='save_humari_radha')],
        [InlineKeyboardButton("Jagadhatri", callback_data='save_jagadhatri')],
        [InlineKeyboardButton("Jaane Anjaane Hum Mile", callback_data='save_jaane_anjaane')],
        [InlineKeyboardButton("The Greatest Show on Earth", callback_data='save_greatest_show')]
    ],
    "up_dangal": [
        [InlineKeyboardButton("PATI ANAADI", callback_data='save_pati_anaadi')],
        [InlineKeyboardButton("PATI BHRAMACHARI", callback_data='save_pati_bhramachari')],
        [InlineKeyboardButton("MANN ATISUNDAR", callback_data='save_mann_atisundar')],
        [InlineKeyboardButton("RIMJHIM", callback_data='save_rimjhim')],
        [InlineKeyboardButton("ISHQ JUNOONI", callback_data='save_ishq_junooni')],
        [InlineKeyboardButton("TEES KE PAAR JAB MILA PYAR", callback_data='save_tees_ke_paar')],
        [InlineKeyboardButton("KAISI TERI DILLAGI", callback_data='save_kaisi_teri')],
        [InlineKeyboardButton("MANN SUNDAR", callback_data='save_mann_sundar')]
    ],
    "up_hotstar": [
        [InlineKeyboardButton("Oh Humnava - Tum Dena Saath Mera", callback_data='save_oh_humnava')],
        [InlineKeyboardButton("Bareilly Ke Bacchan", callback_data='save_bareilly')],
        [InlineKeyboardButton("Tuu Juliet Jatt Di", callback_data='save_juliet')],
        [InlineKeyboardButton("Mahadev & Sons", callback_data='save_mahadev')],
        [InlineKeyboardButton("Juhi Mui", callback_data='save_juhi_mui')],
        [InlineKeyboardButton("Do Duniya Ek Dil", callback_data='save_do_duniya')],
        [InlineKeyboardButton("Mr and Mrs Parshuram", callback_data='save_parshuram')],
        [InlineKeyboardButton("Anupama", callback_data='save_anupama')],
        [InlineKeyboardButton("Yeh Rishta Kya Kehlata Hai", callback_data='save_yrkkh')],
        [InlineKeyboardButton("Sairaab", callback_data='save_sairaab')],
        [InlineKeyboardButton("Mannat - Har Khushi Paane Ki", callback_data='save_mannat')],
        [InlineKeyboardButton("Seher Hone Ko Hai", callback_data='save_seher')],
        [InlineKeyboardButton("Dr Aarambhi", callback_data='save_aarambhi')],
        [InlineKeyboardButton("Udne Ki Aasha", callback_data='save_udne_ki_aasha')],
        [InlineKeyboardButton("Kyunki Saas Bhi Kabhi Bahu Thi", callback_data='save_kyunki_saas')],
        [InlineKeyboardButton("Kyunki Rishton Ke Bhi Roop Badalte Hain", callback_data='save_kyunki_rishton')]
    ],
    "up_sonyliv": [
        [InlineKeyboardButton("Hui Gumm Yaadein", callback_data='save_hui_gumm')],
        [InlineKeyboardButton("TMKOC", callback_data='save_tmkoc')],
        [InlineKeyboardButton("Hastinapur Ke Veer", callback_data='save_hastinapur')],
        [InlineKeyboardButton("Tum Ho Naa", callback_data='save_tum_ho_naa')],
        [InlineKeyboardButton("Pushpa Impossible", callback_data='save_pushpa')]
    ],
    "up_sunnxt": [
        [InlineKeyboardButton("Thodi Si Umeed Thoda Sa Aasman", callback_data='save_thodi_si_umeed')],
        [InlineKeyboardButton("Divya Prem", callback_data='save_divya_prem')]
    ]
}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text("नमस्ते भाई! कृपया कोई तारीख लिखकर भेजें (जैसे: 24 July 2026)।")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    
    if context.user_data.get('awaiting_upload_date'):
        context.user_data['upload_target_date'] = text.lower()
        context.user_data['awaiting_upload_date'] = False
        
        buttons = [
            [InlineKeyboardButton("Hotstar Shows", callback_data='up_hotstar')],
            [InlineKeyboardButton("Zee5 Shows", callback_data='up_zee5')],
            [InlineKeyboardButton("DangalPlay Shows", callback_data='up_dangal')],
            [InlineKeyboardButton("SonyLiv Shows", callback_data='up_sonyliv')],
            [InlineKeyboardButton("SunNXT Shows", callback_data='up_sunnxt')]
        ]
        
        await update.message.reply_text(
            f"📅 तारीख सेट हो गई: {text.title()}\n\nअब यह वीडियो किस OTT Platform के शो की है, चुनें:",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="Markdown"
        )
        return

    months = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]
    has_valid_month = any(m in text.lower() for m in months)
    has_digits = bool(re.search(r'\d+', text))
    
    if not (has_valid_month and has_digits):
        error_msg = (
            "❌ अमान्य तारीख (Invalid Date)!\n\n"
            "कृपया सही फॉर्मेट में तारीख लिखकर भेजें।\n\n"
            "💡 उदाहरण (Example):\n"
            "• 20 July 2026\n"
            "• 24 July 2026\n"
        )
        await update.message.reply_text(error_msg, parse_mode="Markdown")
        return

    context.user_data['selected_date'] = text.lower()
    
    response_text = (
        f"✅ Data fetched successfully!\n\n"
        f"📅 Date Requested:\n{text.title()}\n\n"
        f"📦 Available OTTs in Database:\n5 OTTs found\n\n"
        f"🔍 Please choose your desired OTT below:"
    )
    
    buttons = [
        [InlineKeyboardButton("SunNXT", callback_data='sunnxt_p1')],
        [InlineKeyboardButton("Zee5", callback_data='zee5_p1')],
        [InlineKeyboardButton("DangalPlay", callback_data='dangal_p1')],
        [InlineKeyboardButton("Hotstar(StarPlus & Colors)", callback_data='hotstar_p1')],
        [InlineKeyboardButton("SonyLiv", callback_data='sonyliv_p1')],
        [InlineKeyboardButton("❌ Close", callback_data='close')]
    ]
    
    await update.message.reply_text(response_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))

async def handle_video_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.video:
        file_id = update.message.video.file_id
        raw_name = update.message.caption or update.message.video.file_name or ""
        cleaned_name = raw_name.replace("TvShowHub", "DKLR_DR").replace("tvshowhub", "DKLR_DR")
        
        if not cleaned_name:
            cleaned_name = "Episode_Video.DKLR_DR.mp4"

        final_caption = (
            f"{cleaned_name}\n\n"
            f"⚡️Join :- [ @DKLR_DR ]\n\n"
            f"📌 Join: https://t.me/+AT1UIPpK3c04MTk1\n\n"
            f"📌 Upcoming New Episode - https://t.me/+sN83w5txQO9hNTdl"
        )
        
        if 'pending_videos' not in context.user_data:
            context.user_data['pending_videos'] = []
            
        context.user_data['pending_videos'].append({'id': file_id, 'caption': final_caption})
        context.user_data['awaiting_upload_date'] = True
        
        total_rec = len(context.user_data['pending_videos'])
        await update.message.reply_text(
            f"🎥 वीडियो प्राप्त हो गई! (कुल: {total_rec})\n\n"
            f"✍️ कृपया वह तारीख (Date) लिखकर भेजें जिस तारीख का यह एपिसोड है:\n"
            f"*(उदाहरण: 20 July 2026)*",
            parse_mode="Markdown"
        )

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_date = context.user_data.get('selected_date', '')
    
    if data == 'close':
        await query.message.delete()
        return
        
    elif data == 'back_ott':
        buttons = [
            [InlineKeyboardButton("SunNXT", callback_data='sunnxt_p1')],
            [InlineKeyboardButton("Zee5", callback_data='zee5_p1')],
            [InlineKeyboardButton("DangalPlay", callback_data='dangal_p1')],
            [InlineKeyboardButton("Hotstar(StarPlus & Colors)", callback_data='hotstar_p1')],
            [InlineKeyboardButton("SonyLiv", callback_data='sonyliv_p1')],
            [InlineKeyboardButton("❌ Close", callback_data='close')]
        ]
        await query.message.edit_text(
            f"✅ Data fetched successfully!\n\n📅 Date Requested:\n{user_date.title()}\n\n🔍 Please choose your desired OTT below:",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="Markdown"
        )
        return

    elif data in UPLOAD_SHOWS:
        await query.message.edit_text(
            "🎯 कृपया शो चुनें जिसके लिए यह वीडियो/वीडियोस सेट करनी हैं:",
            reply_markup=InlineKeyboardMarkup(UPLOAD_SHOWS[data])
        )
        return

    elif data.startswith('save_'):
        show_key = data.replace('save_', '')
        pending = context.user_data.get('pending_videos', [])
        target_date = context.user_data.get('upload_target_date', '')
        
        if pending and target_date:
            if target_date not in VIDEO_DATABASE:
                VIDEO_DATABASE[target_date] = {}
            if show_key not in VIDEO_DATABASE[target_date]:
                VIDEO_DATABASE[target_date][show_key] = []
                
            VIDEO_DATABASE[target_date][show_key].extend(pending)
            show_name = SHOW_NAME_MAP.get(show_key, show_key.replace('_', ' ').title())
            
            total_count = len(VIDEO_DATABASE[target_date][show_key])
            context.user_data['pending_videos'] = []
            context.user_data['upload_target_date'] = ''
            
            await query.message.edit_text(
                f"✅ अपलोड सफल!\n\n"
                f"📅 तारीख: {target_date.title()}\n"
                f"📺 शो: {show_name}\n"
                f"🎥 कुल लिंक्ड वीडियोस: {total_count}\n\n"
                f"यह वीडियो सिर्फ {target_date.title()} सर्च करने पर ही मिलेगी! 🎉"
            )
        else:
            await query.message.edit_text("❌ त्रुटि! कृपया पहले वीडियो भेजें।")
        return

    elif data in OTT_SHOWS_MAP:
        ott_name = data.split('_')[0].upper()
        all_shows = OTT_SHOWS_MAP[data]
        date_db = VIDEO_DATABASE.get(user_date, {})
        
        show_buttons = []
        for key in all_shows:
            if key in date_db and len(date_db[key]) > 0:
                s_name = SHOW_NAME_MAP.get(key, key)
                show_buttons.append([InlineKeyboardButton(f"{s_name} ↗️", callback_data=f'show_{key}')])
                
        if show_buttons:
            show_buttons.append([InlineKeyboardButton("⬅️ Choose OTT", callback_data='back_ott'), InlineKeyboardButton("❌ Close", callback_data='close')])
            
            text = (
                f"🎬 {ott_name} Shows\n\n"
                f"🍿 Chosen OTT: {ott_name}\n"
                f"📅 Chosen Date: {user_date.title()}\n\n"
                f"🎯 Choose a Show Below:"
            )
            await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(show_buttons), parse_mode="Markdown")
        else:
            await query.message.reply_text("❌ No data found for that date.")
        
    elif data.startswith('show_'):
        show_key = data.replace('show_', '')
        date_db = VIDEO_DATABASE.get(user_date, {})
        video_list = date_db.get(show_key, [])
        
        if video_list:
            await query.message.delete()
            
            for vid_obj in video_list:
                await context.bot.send_video(
                    chat_id=query.message.chat_id, 
                    video=vid_obj['id'],
                    caption=vid_obj['caption']
                )
                
            notice_text = (
                "╭─────── ‼️ Auto-Delete Notice ‼️ ───────╮\n\n"
                "🚨 Make sure to save the video!\n"
                "⏰ Videos Will Be Auto-deleted After 60 minutes to avoid copyright issue ⌛\n"
                "📬 Forward it to Saved Messages and Watch there\n\n"
                "╰────────────────────────────────────╯"
            )
            await context.bot.send_message(chat_id=query.message.chat_id, text=notice_text, parse_mode="Markdown")
        else:
            await query.message.reply_text("❌ No data found for that date.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video_upload))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(button_click))
    
    print("आपका ऑल-इन-वन बोट चालू हो गया है...")
    app.run_polling()

import os
import nest_asyncio
nest_asyncio.apply()

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CommandHandler,
    ConversationHandler, ContextTypes, filters
)
from pydub import AudioSegment

TOKEN = "7409180727:AAHsOZp0L8N9drBSXgHl5TRiQT9V_X98luA"

LANGUAGES = {
    "en": {
        "welcome": "👋 Welcome, {name}!\nThis bot converts your voice or video files to mp3, wav, or ogg formats.\nYou have {count} conversions left today.",
        "main_menu": "🎛️ Main Menu",
        "convert": "🎵 Convert Audio/Video",
        "change_lang": "🌐 Change Language",
        "activate_premium": "💎 Activate Premium",
        "show_quota": "📊 Daily Quota",
        "help": "❓ Help",
        "ask_format": "Choose format to convert:",
        "ask_filename": "Please enter a name for the output file:",
        "processing": "⏳ Processing your file...",
        "done": "✅ Done! Here is your file:",
        "quota": "🔢 You have {count} conversions left today.",
        "limit_reached": "⚠️ You reached your daily limit. Activate premium for more conversions.",
        "enter_code": "Please enter your premium code:",
        "premium_ok": "🎉 Premium activated! Your quota is now {count}.",
        "premium_fail": "❌ Invalid code or expired.",
        "choose_lang": "Select your language:",
        "cancel": "Cancel",
        "back": "⬅️ Back",
        "help_text": "Send a voice or video, choose a format, enter a name, and you will get a downloadable file. Use the menu for more options.",
        "invalid_file": "❗ Please send a voice, audio, or video file.",
        "ask_feature": "What do you want to do with this file?",
        "enter_filename_button": "✏️ Enter file name",
        "convert_button": "🎵 Convert format",
    },
    "ar": {
        "welcome": "👋 أهلاً {name}!\nهذا البوت يحول الصوت أو الفيديو إلى mp3 أو wav أو ogg.\nلديك {count} تحويلات متبقية اليوم.",
        "main_menu": "🎛️ القائمة الرئيسية",
        "convert": "🎵 تحويل صوت/فيديو",
        "change_lang": "🌐 تغيير اللغة",
        "activate_premium": "💎 تفعيل العضوية المميزة",
        "show_quota": "📊 العداد اليومي",
        "help": "❓ تعليمات",
        "ask_format": "اختر الصيغة:",
        "ask_filename": "أدخل اسم الملف النهائي:",
        "processing": "⏳ جارى معالجة الملف...",
        "done": "✅ تم! هذا هو ملفك:",
        "quota": "🔢 لديك {count} تحويلات متبقية اليوم.",
        "limit_reached": "⚠️ وصلت إلى الحد اليومي. فعل العضوية المميزة لتحويلات أكثر.",
        "enter_code": "أدخل كود العضوية المميزة:",
        "premium_ok": "🎉 تم تفعيل العضوية! حصتك الآن {count}.",
        "premium_fail": "❌ الكود غير صحيح أو منتهي.",
        "choose_lang": "اختر لغتك:",
        "cancel": "إلغاء",
        "back": "⬅️ رجوع",
        "help_text": "أرسل مقطع صوت أو فيديو، اختر الصيغة، أدخل اسم الملف، وستحصل على ملف قابل للتحميل. استخدم القائمة للمزيد.",
        "invalid_file": "❗ أرسل ملف صوت أو فيديو فقط.",
        "ask_feature": "ما الذي تريد فعله بهذا الملف؟",
        "enter_filename_button": "✏️ إدخال اسم الملف",
        "convert_button": "🎵 تحويل الصيغة",
    },
    "id": {
        "welcome": "👋 Selamat datang, {name}!\nBot ini mengonversi suara atau video ke format mp3, wav, atau ogg.\nKamu punya {count} konversi hari ini.",
        "main_menu": "🎛️ Menu Utama",
        "convert": "🎵 Konversi Audio/Video",
        "change_lang": "🌐 Ganti Bahasa",
        "activate_premium": "💎 Aktifkan Premium",
        "show_quota": "📊 Kuota Harian",
        "help": "❓ Bantuan",
        "ask_format": "Pilih format:",
        "ask_filename": "Masukkan nama file output:",
        "processing": "⏳ Memproses file...",
        "done": "✅ Selesai! Berikut file kamu:",
        "quota": "🔢 Kamu punya {count} konversi hari ini.",
        "limit_reached": "⚠️ Kuota harian habis. Aktifkan premium untuk lebih banyak konversi.",
        "enter_code": "Masukkan kode premium:",
        "premium_ok": "🎉 Premium diaktifkan! Kuota kamu sekarang {count}.",
        "premium_fail": "❌ Kode tidak valid atau kadaluarsa.",
        "choose_lang": "Pilih bahasa:",
        "cancel": "Batal",
        "back": "⬅️ Kembali",
        "help_text": "Kirim suara atau video, pilih format, masukkan nama file, dan kamu akan mendapatkan file yang dapat diunduh. Gunakan menu untuk opsi lainnya.",
        "invalid_file": "❗ Kirim file suara atau video.",
        "ask_feature": "Apa yang ingin kamu lakukan dengan file ini?",
        "enter_filename_button": "✏️ Masukkan nama file",
        "convert_button": "🎵 Konversi format",
    }
}

DAILY_QUOTA = 10
PREMIUM_QUOTA = 100
PREMIUM_CODES = {}
USER_DATA = {}

(
    MAIN_MENU,
    WAIT_FILE,
    WAIT_FORMAT,
    WAIT_FILENAME,
    WAIT_PREMIUM,
    WAIT_LANGUAGE,
    PROCESSING
) = range(7)

def get_lang(user_id):
    return USER_DATA.get(user_id, {}).get("lang", "en")

def get_text(user_id, key, **kwargs):
    lang = get_lang(user_id)
    text = LANGUAGES[lang][key]
    return text.format(**kwargs)

def get_menu_keyboard(user_id):
    lang = get_lang(user_id)
    return ReplyKeyboardMarkup([
        [LANGUAGES[lang]["convert"]],
        [LANGUAGES[lang]["show_quota"], LANGUAGES[lang]["activate_premium"]],
        [LANGUAGES[lang]["change_lang"], LANGUAGES[lang]["help"]],
    ], resize_keyboard=True)

def get_lang_keyboard():
    return ReplyKeyboardMarkup([
        [LANGUAGES["en"]["choose_lang"], LANGUAGES["ar"]["choose_lang"], LANGUAGES["id"]["choose_lang"]],
        ["Cancel"]
    ], resize_keyboard=True)

def get_format_keyboard(user_id):
    lang = get_lang(user_id)
    return ReplyKeyboardMarkup([
        ["mp3", "wav", "ogg"],
        [LANGUAGES[lang]["cancel"]]
    ], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {
            "quota": DAILY_QUOTA,
            "lang": user.language_code if user.language_code in LANGUAGES else "en",
            "premium": False
        }
    name = user.first_name or user.username or "User"
    text = get_text(user_id, "welcome", name=name, count=USER_DATA[user_id]["quota"])
    await update.message.reply_text(text, reply_markup=get_menu_keyboard(user_id))
    return MAIN_MENU

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_text(update.effective_user.id, "main_menu"), reply_markup=get_menu_keyboard(update.effective_user.id))
    return MAIN_MENU

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_text(update.effective_user.id, "help_text"), reply_markup=get_menu_keyboard(update.effective_user.id))
    return MAIN_MENU

async def show_quota(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(get_text(user_id, "quota", count=USER_DATA[user_id]["quota"]), reply_markup=get_menu_keyboard(user_id))
    return MAIN_MENU

async def change_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌐 Choose your language:", reply_markup=ReplyKeyboardMarkup([
        ["English", "العربية", "Indonesia"],
        ["Cancel"]
    ], resize_keyboard=True))
    return WAIT_LANGUAGE

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang_map = {"English": "en", "العربية": "ar", "Indonesia": "id"}
    choice = update.message.text
    user_id = update.effective_user.id
    if choice in lang_map:
        USER_DATA[user_id]["lang"] = lang_map[choice]
        await update.message.reply_text(get_text(user_id, "main_menu"), reply_markup=get_menu_keyboard(user_id))
        return MAIN_MENU
    else:
        await update.message.reply_text(get_text(user_id, "main_menu"), reply_markup=get_menu_keyboard(user_id))
        return MAIN_MENU

async def activate_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_text(update.effective_user.id, "enter_code"))
    return WAIT_PREMIUM

async def premium_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    user_id = update.effective_user.id
    if code in PREMIUM_CODES:
        USER_DATA[user_id]["premium"] = True
        USER_DATA[user_id]["quota"] = PREMIUM_CODES[code]["quota"]
        await update.message.reply_text(get_text(user_id, "premium_ok", count=USER_DATA[user_id]["quota"]), reply_markup=get_menu_keyboard(user_id))
        return MAIN_MENU
    else:
        await update.message.reply_text(get_text(user_id, "premium_fail"), reply_markup=get_menu_keyboard(user_id))
        return MAIN_MENU

async def convert_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_text(update.effective_user.id, "invalid_file"), reply_markup=get_menu_keyboard(update.effective_user.id))
    return WAIT_FILE

async def file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if USER_DATA[user_id]["quota"] <= 0 and not USER_DATA[user_id]["premium"]:
        await update.message.reply_text(get_text(user_id, "limit_reached"), reply_markup=get_menu_keyboard(user_id))
        return MAIN_MENU

    message = update.message
    file = None
    file_type = None
    if message.voice:
        file = await context.bot.get_file(message.voice.file_id)
        file_type = "voice"
        context.user_data["input_file"] = f"voice_{message.voice.file_unique_id}.ogg"
    elif message.audio:
        file = await context.bot.get_file(message.audio.file_id)
        file_type = "audio"
        context.user_data["input_file"] = message.audio.file_name or f"audio_{message.audio.file_unique_id}.mp3"
    elif message.video:
        file = await context.bot.get_file(message.video.file_id)
        file_type = "video"
        context.user_data["input_file"] = f"video_{message.video.file_unique_id}.mp4"
    else:
        await message.reply_text(get_text(user_id, "invalid_file"), reply_markup=get_menu_keyboard(user_id))
        return WAIT_FILE

    await file.download_to_drive(context.user_data["input_file"])
    context.user_data["file_type"] = file_type

    await message.reply_text(get_text(user_id, "ask_format"), reply_markup=get_format_keyboard(user_id))
    return WAIT_FORMAT

async def format_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fmt = update.message.text
    user_id = update.effective_user.id
    if fmt not in ["mp3", "wav", "ogg"]:
        await update.message.reply_text(get_text(user_id, "ask_format"), reply_markup=get_format_keyboard(user_id))
        return WAIT_FORMAT

    context.user_data["output_format"] = fmt
    await update.message.reply_text(get_text(user_id, "ask_filename"), reply_markup=ReplyKeyboardMarkup([
        [LANGUAGES[get_lang(user_id)]["cancel"]]
    ], resize_keyboard=True))
    return WAIT_FILENAME

async def filename_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    filename = update.message.text.strip()
    user_id = update.effective_user.id
    if filename == LANGUAGES[get_lang(user_id)]["cancel"]:
        await update.message.reply_text(get_text(user_id, "main_menu"), reply_markup=get_menu_keyboard(user_id))
        return MAIN_MENU

    input_file = context.user_data.get("input_file")
    output_format = context.user_data.get("output_format")
    file_type = context.user_data.get("file_type")
    output_file = f"{filename}.{output_format}"

    await update.message.reply_text(get_text(user_id, "processing"))

    try:
        if file_type in ["voice", "audio"]:
            audio = AudioSegment.from_file(input_file)
            audio.export(output_file, format=output_format)
        elif file_type == "video":
            audio = AudioSegment.from_file(input_file)
            audio.export(output_file, format=output_format)
        else:
            raise Exception("Unsupported file type")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}", reply_markup=get_menu_keyboard(user_id))
        if os.path.exists(input_file):
            os.remove(input_file)
        return MAIN_MENU

    with open(output_file, "rb") as f:
        await update.message.reply_document(
            f,
            filename=output_file,
            caption=get_text(user_id, "done")
        )

    if not USER_DATA[user_id].get("premium", False):
        USER_DATA[user_id]["quota"] -= 1

    if os.path.exists(input_file):
        os.remove(input_file)
    if os.path.exists(output_file):
        os.remove(output_file)

    await update.message.reply_text(get_text(user_id, "quota", count=USER_DATA[user_id]["quota"]), reply_markup=get_menu_keyboard(user_id))
    return MAIN_MENU

async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_text(update.effective_user.id, "main_menu"), reply_markup=get_menu_keyboard(update.effective_user.id))
    return MAIN_MENU

async def run_bot(app):
    await app.initialize()
    await app.start()
    await app.updater.start_polling()

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [
                MessageHandler(filters.Regex(LANGUAGES["en"]["convert"]) | filters.Regex(LANGUAGES["ar"]["convert"]) | filters.Regex(LANGUAGES["id"]["convert"]), convert_cmd),
                MessageHandler(filters.Regex(LANGUAGES["en"]["show_quota"]) | filters.Regex(LANGUAGES["ar"]["show_quota"]) | filters.Regex(LANGUAGES["id"]["show_quota"]), show_quota),
                MessageHandler(filters.Regex(LANGUAGES["en"]["activate_premium"]) | filters.Regex(LANGUAGES["ar"]["activate_premium"]) | filters.Regex(LANGUAGES["id"]["activate_premium"]), activate_premium),
                MessageHandler(filters.Regex(LANGUAGES["en"]["help"]) | filters.Regex(LANGUAGES["ar"]["help"]) | filters.Regex(LANGUAGES["id"]["help"]), help_cmd),
                MessageHandler(filters.Regex(LANGUAGES["en"]["change_lang"]) | filters.Regex(LANGUAGES["ar"]["change_lang"]) | filters.Regex(LANGUAGES["id"]["change_lang"]), change_lang),
                MessageHandler(filters.VOICE | filters.AUDIO | filters.VIDEO, file_handler)
            ],
            WAIT_FILE: [
                MessageHandler(filters.VOICE | filters.AUDIO | filters.VIDEO, file_handler),
                MessageHandler(filters.Regex("Cancel") | filters.Regex("إلغاء") | filters.Regex("Batal"), cancel_handler),
            ],
            WAIT_FORMAT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, format_handler),
                MessageHandler(filters.Regex("Cancel") | filters.Regex("إلغاء") | filters.Regex("Batal"), cancel_handler),
            ],
            WAIT_FILENAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, filename_handler),
                MessageHandler(filters.Regex("Cancel") | filters.Regex("إلغاء") | filters.Regex("Batal"), cancel_handler),
            ],
            WAIT_LANGUAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_language)
            ],
            WAIT_PREMIUM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, premium_code)
            ]
        },
        fallbacks=[MessageHandler(filters.Regex("Cancel") | filters.Regex("إلغاء") | filters.Regex("Batal"), cancel_handler)],
        allow_reentry=True
    )

    app.add_handler(conv_handler)
    print("Bot is running...")

    import asyncio
    asyncio.run(run_bot(app))

if __name__ == "__main__":
    main()
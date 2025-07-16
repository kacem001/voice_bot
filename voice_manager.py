import os
import json
import random
import string
from datetime import datetime, timedelta
import re
import nest_asyncio
nest_asyncio.apply()

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CommandHandler,
    ContextTypes, ConversationHandler, filters
)

ADMIN_IDS = [6413712599]  # معرفك + يمكنك إضافة معرفات أخرى هنا
TOKEN = "8036777818:AAHqETTgKaQezN_iy7QadyvBpR8zkLo5qKk"
CODES_FILE = "premium_codes.json"

(
    MAIN_MENU,
    WAIT_DAYS,
    WAIT_SELECT_CODE,
    WAIT_EXTEND_DAYS,
    WAIT_REMOVE_CODE
) = range(5)

def load_codes():
    if not os.path.exists(CODES_FILE):
        return {}
    with open(CODES_FILE, "r") as f:
        return json.load(f)

def save_codes(codes):
    with open(CODES_FILE, "w") as f:
        json.dump(codes, f, indent=2)

def generate_code(length=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Access Denied.")
        return ConversationHandler.END
    await update.message.reply_text("🛡️ Admin Panel\nاختر العملية:", reply_markup=ReplyKeyboardMarkup([
        ["➕ توليد كود جديد", "📋 عرض الأكواد"],
        ["⏳ تمديد كود", "❌ حذف كود"],
        ["🔄 إعادة تحميل", "⏹️ خروج"]
    ], resize_keyboard=True))
    return MAIN_MENU

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await start(update, context)

async def reload_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("تم إعادة تحميل اللوحة.")
    return await start(update, context)

async def exit_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("تم الخروج 👋")
    return ConversationHandler.END

async def generate_code_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أدخل عدد الأيام لصلاحية الكود (مثال: 30):")
    return WAIT_DAYS

async def generate_code_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # إصلاح إدخال الرقم: يقبل أول رقم صحيح فقط من الرسالة
        match = re.search(r'\d+', update.message.text)
        days = int(match.group()) if match else None
        if not days or days <= 0:
            raise ValueError("days must be positive")
        code = generate_code()
        expire_date = (datetime.utcnow() + timedelta(days=days)).strftime("%Y-%m-%d")
        codes = load_codes()
        codes[code] = {"quota": 100, "expire": expire_date, "active": True}
        save_codes(codes)
        await update.message.reply_text(
            f"تم توليد كود بريميوم:\nCode: `{code}`\nينتهي في: {expire_date}",
            reply_markup=ReplyKeyboardMarkup([["العودة للقائمة"]], resize_keyboard=True),
            parse_mode="Markdown"
        )
        return MAIN_MENU
    except Exception as e:
        await update.message.reply_text("إدخال غير صحيح. أدخل رقم فقط (مثال: 30):")
        return WAIT_DAYS

async def list_codes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    codes = load_codes()
    if not codes:
        await update.message.reply_text("لا توجد أكواد بعد.", reply_markup=ReplyKeyboardMarkup([["العودة للقائمة"]], resize_keyboard=True))
        return MAIN_MENU
    msg = "🗂️ الأكواد المتوفرة:\n"
    for c, d in codes.items():
        msg += f"\nCode: `{c}`\nQuota: {d['quota']}\nExpire: {d['expire']}\nActive: {d.get('active', True)}\n---"
    await update.message.reply_text(msg, reply_markup=ReplyKeyboardMarkup([["العودة للقائمة"]], resize_keyboard=True), parse_mode="Markdown")
    return MAIN_MENU

async def extend_code_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    codes = load_codes()
    if not codes:
        await update.message.reply_text("لا توجد أكواد لتمديدها.", reply_markup=ReplyKeyboardMarkup([["العودة للقائمة"]], resize_keyboard=True))
        return MAIN_MENU
    context.user_data["codes"] = list(codes.keys())
    keyboard = [[c] for c in context.user_data["codes"]]
    keyboard.append(["العودة للقائمة"])
    await update.message.reply_text("اختر الكود الذي تريد تمديده:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return WAIT_SELECT_CODE

async def extend_code_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    if code == "العودة للقائمة":
        return await start(update, context)
    codes = load_codes()
    if code not in codes:
        await update.message.reply_text("كود غير صحيح. اختر من القائمة:")
        return WAIT_SELECT_CODE
    context.user_data["extend_code"] = code
    await update.message.reply_text("أدخل عدد الأيام التي تريد إضافتها:")
    return WAIT_EXTEND_DAYS

async def extend_code_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        match = re.search(r'\d+', update.message.text)
        days = int(match.group()) if match else None
        if not days or days <= 0:
            raise ValueError("days must be positive")
        code = context.user_data["extend_code"]
        codes = load_codes()
        expire = datetime.strptime(codes[code]["expire"], "%Y-%m-%d")
        new_expire = (expire + timedelta(days=days)).strftime("%Y-%m-%d")
        codes[code]["expire"] = new_expire
        save_codes(codes)
        await update.message.reply_text(
            f"تم تمديد الكود `{code}` حتى {new_expire}",
            reply_markup=ReplyKeyboardMarkup([["العودة للقائمة"]], resize_keyboard=True),
            parse_mode="Markdown"
        )
        return MAIN_MENU
    except:
        await update.message.reply_text("إدخال غير صحيح. أدخل رقم فقط:")
        return WAIT_EXTEND_DAYS

async def remove_code_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    codes = load_codes()
    if not codes:
        await update.message.reply_text("لا توجد أكواد للحذف.", reply_markup=ReplyKeyboardMarkup([["العودة للقائمة"]], resize_keyboard=True))
        return MAIN_MENU
    context.user_data["codes"] = list(codes.keys())
    keyboard = [[c] for c in context.user_data["codes"]]
    keyboard.append(["العودة للقائمة"])
    await update.message.reply_text("اختر الكود الذي تريد حذفه:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return WAIT_REMOVE_CODE

async def remove_code_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    if code == "العودة للقائمة":
        return await start(update, context)
    codes = load_codes()
    if code not in codes:
        await update.message.reply_text("كود غير صحيح. اختر من القائمة:")
        return WAIT_REMOVE_CODE
    codes.pop(code)
    save_codes(codes)
    await update.message.reply_text(
        f"تم حذف الكود `{code}`.",
        reply_markup=ReplyKeyboardMarkup([["العودة للقائمة"]], resize_keyboard=True),
        parse_mode="Markdown"
    )
    return MAIN_MENU

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [
                MessageHandler(filters.Regex("توليد كود جديد"), generate_code_start),
                MessageHandler(filters.Regex("عرض الأكواد"), list_codes),
                MessageHandler(filters.Regex("تمديد كود"), extend_code_start),
                MessageHandler(filters.Regex("حذف كود"), remove_code_start),
                MessageHandler(filters.Regex("إعادة تحميل"), reload_menu),
                MessageHandler(filters.Regex("خروج"), exit_handler),
                MessageHandler(filters.Regex("العودة للقائمة"), main_menu),
            ],
            WAIT_DAYS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, generate_code_days)
            ],
            WAIT_SELECT_CODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, extend_code_select)
            ],
            WAIT_EXTEND_DAYS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, extend_code_days)
            ],
            WAIT_REMOVE_CODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, remove_code_select)
            ],
        },
        fallbacks=[MessageHandler(filters.Regex("العودة للقائمة"), main_menu)],
        allow_reentry=True
    )
    app.add_handler(conv_handler)
    import asyncio
    asyncio.run(app.initialize())
    asyncio.run(app.start())
    asyncio.run(app.updater.start_polling())

if __name__ == "__main__":
    main()
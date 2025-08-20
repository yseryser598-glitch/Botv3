import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    JobQueue,
)
from flask import Flask, request
from datetime import datetime, timedelta

# --- Logging ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

# --- Variabile de mediu ---
TOKEN = os.environ.get("BOT_TOKEN")
PORT = int(os.environ.get("PORT", "10000"))
LOG_CHAT_ID = os.environ.get("LOG_CHAT_ID")  # optional pentru log

# --- Mesaje default ---
welcome_message = "Bine ai venit în grup! Respectă regulile."
rules_message = "Regulile grupului: 1) Fără spam 2) Fără link-uri 3) Respect mutual"

# --- Flask pentru webhook ---
app = Flask(__name__)

# --- Handlere și funcții bot ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Botul este activ!")

# Welcome personalizat
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.new_chat_members:
        for new_member in update.message.new_chat_members:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=welcome_message
            )

# Anti-link cu ban permanent
async def check_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text and ("http://" in update.message.text or "https://" in update.message.text):
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=update.message.message_id
            )
            await context.bot.ban_chat_member(
                chat_id=update.effective_chat.id,
                user_id=update.message.from_user.id
            )
            if LOG_CHAT_ID:
                await context.bot.send_message(
                    chat_id=LOG_CHAT_ID,
                    text=f"Blocked {update.message.from_user.username} for posting a link."
                )
        except Exception as e:
            logging.error(e)

# Comandă pentru setarea mesajului welcome
async def set_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global welcome_message
    if context.args:
        welcome_message = " ".join(context.args)
        await update.message.reply_text(f"Mesajul de welcome a fost actualizat:\n{welcome_message}")
    else:
        await update.message.reply_text("Folosire: /setwelcome [mesaj]")

# Comandă pentru setarea mesajului reguli
async def set_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global rules_message
    if context.args:
        rules_message = " ".join(context.args)
        await update.message.reply_text(f"Mesajul cu reguli a fost actualizat:\n{rules_message}")
    else:
        await update.message.reply_text("Folosire: /setrules [mesaj]")

# Funcție pentru trimitere reguli periodic
async def send_rules_periodically(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=context.job.chat_id, text=rules_message)

# Comandă pentru a porni trimiterea regulilor periodic
async def startrules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    interval_hours = 2  # schimbă după cum vrei
    context.job_queue.run_repeating(
        send_rules_periodically, interval=interval_hours*3600, first=0, chat_id=chat_id
    )
    await update.message.reply_text(f"Mesajele cu reguli vor fi trimise la fiecare {interval_hours} ore.")

# --- Construiește aplicația ---
application = ApplicationBuilder().token(TOKEN).build()

# --- Handlere ---
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("setwelcome", set_welcome))
application.add_handler(CommandHandler("setrules", set_rules))
application.add_handler(CommandHandler("startrules", startrules))
application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), check_links))

# --- Webhook Flask endpoint ---
@app.route(f"/{TOKEN}", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    await application.update_queue.put(update)
    return "ok"

# --- Pornește aplicația Flask + job_queue ---
if __name__ == "__main__":
    import asyncio
    from threading import Thread

    def run_application():
        application.run_polling(stop_signals=None)

    Thread(target=run_application).start()
    app.run(host="0.0.0.0", port=PORT)

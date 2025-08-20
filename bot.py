import os
import logging
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from threading import Timer

# --- Configurare logging ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

# --- Variabile de mediu ---
TOKEN = os.environ.get("BOT_TOKEN")
LOG_CHAT_ID = os.environ.get("LOG_CHAT_ID")  # optional
PORT = int(os.environ.get("PORT", "10000"))

# --- Creează bot și updater ---
bot = Bot(token=TOKEN)
updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

# --- Mesaje ---
WELCOME_MESSAGE = "Bine ai venit în grup! Respectă regulile."
RULES_MESSAGE = "Regulile grupului: 1) Fără spam 2) Fără link-uri 3) Respect mutual"

# --- Funcții ---
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Botul este activ!")

def welcome(update: Update, context: CallbackContext):
    for new_member in update.message.new_chat_members:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=WELCOME_MESSAGE
        )

def check_links(update: Update, context: CallbackContext):
    if "http://" in update.message.text or "https://" in update.message.text:
        try:
            context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=update.message.message_id
            )
            context.bot.kick_chat_member(
                chat_id=update.effective_chat.id,
                user_id=update.message.from_user.id
            )
            if LOG_CHAT_ID:
                context.bot.send_message(
                    chat_id=LOG_CHAT_ID,
                    text=f"Blocked {update.message.from_user.username} for posting a link."
                )
        except Exception as e:
            logging.error(e)

def send_rules_periodically(context: CallbackContext):
    context.bot.send_message(chat_id=context.job.context, text=RULES_MESSAGE)

def start_rules(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    interval_hours = 2  # modifică după cum vrei
    context.job_queue.run_repeating(
        send_rules_periodically, interval=interval_hours*3600, first=0, context=chat_id
    )
    update.message.reply_text(f"Mesajele cu reguli vor fi trimise la fiecare {interval_hours} ore.")

# --- Handlere ---
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("startrules", start_rules))
dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, welcome))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, check_links))

# --- Pornește botul ---
if __name__ == "__main__":
    updater.start_polling()
    updater.idle()

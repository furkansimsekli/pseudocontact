import random
import sys

import toml
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

from . import utils
from .database import ContactDatabase

config_path = sys.argv[1] if len(sys.argv) > 1 else "config.toml"
config = toml.load(config_path)
db = ContactDatabase(config["DATABASE_PATH"])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_user.id,
                                   text=f"Welcome to PseudoContact! You can easily store your unnecessary contacts "
                                        f"before deleting them. If they reach you out later on, you won't have a "
                                        f"problem identifying them ;)\n\n"
                                        f"You can add new contacts by using /add command"
                                        f"You can make a query with /find command\n\n"
                                        f"Use /help for more details")


async def help_(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_user.id,
                                   text=f"Lorem ipsum")


async def get_all_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contacts = await db.all(owner=update.effective_user.id)

    if not contacts:
        await context.bot.send_message(chat_id=update.effective_user.id,
                                       text="No user found!")
        return

    message = utils.create_result_message(contacts)
    await context.bot.send_message(chat_id=update.effective_user.id,
                                   text=message,
                                   parse_mode=ParseMode.HTML)


async def add_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_user.id,
                                   text=f"I'll ask a few questions. What's the name of your new contact?\n"
                                        f"You can use /cancel anytime to abort the process..")
    return 1


async def save_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    context.user_data["contact_name"] = name
    await context.bot.send_message(chat_id=update.effective_user.id,
                                   text=f"Nice! The name you entered was {name}.\n"
                                        f"Now tell me the number, it can be in any format but come on.. "
                                        f"<a href='https://en.wikipedia.org/wiki/E.164'>E.164</a> exists.",
                                   parse_mode=ParseMode.HTML,
                                   disable_web_page_preview=True)
    return 2


async def save_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    number = update.message.text.strip()

    if len(number) > 32:
        await context.bot.send_message(chat_id=update.effective_user.id,
                                       text=f"Wow, this is too long! It can't exceed 32 characters.")
        return 1

    context.user_data["contact_number"] = number
    await context.bot.send_message(chat_id=update.effective_user.id,
                                   text=f"Saved! You can clean it up from your ACTUAL contacts mmmhhhh")
    name = context.user_data['contact_name']
    await db.add_new(owner=update.effective_user.id, name=name, number=number)
    return -1


async def find_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_user.id,
                                   text=f"Write the number you want to query or the name you are looking for.")
    return 1


async def query_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    search_term = update.message.text
    contacts = await db.find(owner=update.effective_user.id, search_term=search_term)

    if not contacts:
        await context.bot.send_message(chat_id=update.effective_user.id,
                                       text="No user found!")
        return

    message = utils.create_result_message(contacts)
    await context.bot.send_message(chat_id=update.effective_user.id,
                                   text=message,
                                   parse_mode=ParseMode.HTML)
    return -1


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dad_joke = random.choice([True, False])

    if dad_joke:
        await context.bot.send_message(chat_id=update.effective_user.id,
                                       text="Cancelled. Not on Twitter though")
    else:
        await context.bot.send_message(chat_id=update.effective_user.id,
                                       text="Cancelled.")

    return -1


async def connect_db(context: ContextTypes.DEFAULT_TYPE):
    await db.connect()


def main():
    app = Application.builder().token(config["TELEGRAM_API_KEY"]).build()

    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("add", add_contact)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_name)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_number)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("find", find_contacts)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, query_contact)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    ))

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_))
    app.add_handler(CommandHandler("all", get_all_contacts))
    app.job_queue.run_once(connect_db, 1)

    if config["WEBHOOK_CONNECTED"]:
        app.run_webhook(listen="0.0.0.0",
                        port=int(config["PORT"]),
                        url_path=config["TELEGRAM_API_KEY"],
                        webhook_url=config["WEBHOOK_URL"])
    else:
        app.run_polling()

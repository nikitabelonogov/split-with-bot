import logging
import os

import telegram
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

import static
from DebtsManager import DebtsManager

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)


def parse_mentions(message):
    result = []
    mentions = [x for x in message['entities'] if x['type'] == 'mention']
    for mention in mentions:
        result.append(message['text'][mention['offset']:mention['offset'] + mention['length']])
    return result


def split_command(update: telegram.Update, context: telegram.ext.CallbackContext):
    args = context.args
    lender = '@' + update.message.from_user.username
    name = args[0]
    total = float(args[1])
    debtors = parse_mentions(update.message)
    print(update.message)
    print(debtors)
    response = debts_manager.lend(lender, debtors, name, total, self_except=False)
    update.message.reply_text('\n'.join(map(str, response)) or 'No entries found')


def lend_command(update: telegram.Update, context: telegram.ext.CallbackContext):
    args = context.args
    lender = '@' + update.message.from_user.username
    name = ' '.join(args[2:])
    total = float(args[1])
    debtors = parse_mentions(update.message)
    response = debts_manager.lend(lender, debtors, name, total, self_except=True)
    buttons = [[
        telegram.InlineKeyboardButton("⛔️", callback_data="callback"),
    ]]
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='\n'.join(map(str, response)) or 'No entries found',
        reply_markup=telegram.InlineKeyboardMarkup(buttons),
    )


def history_command(update: telegram.Update, context: telegram.ext.CallbackContext):
    args = context.args
    username = '@' + update.message.from_user.username
    if args:
        username2 = args[0]
        response = debts_manager.related_debts(username, username2)
    else:
        response = debts_manager.related_debts(username)
    update.message.reply_text('\n'.join(map(str, response)) or 'No entries found')


def status_command(update: telegram.Update, context: telegram.ext.CallbackContext):
    args = context.args
    username = '@' + update.message.from_user.username
    if args:
        username2 = args[0]
        debts = debts_manager.related_debts(username, username2)
    else:
        debts = debts_manager.related_debts(username)
    totals = {}
    for debt in debts:
        if debt.lender == username:
            totals[debt.debtor] = totals.get(debt.debtor, 0.) + float(debt)
        elif debt.debtor == username:
            totals[debt.lender] = totals.get(debt.lender, 0.) - float(debt)
    response = []
    for username, total in totals.items():
        if total <= -1.:
            response.append('you owes {} {:.0f}₽ in total'.format(username, -total))
        elif total >= 1.:
            response.append('you lent {} {:.0f}₽ in total'.format(username, total))
    update.message.reply_text('\n'.join(map(str, response)) or 'No entries found')


def delete_command(update: telegram.Update, context: telegram.ext.CallbackContext):
    args = context.args
    username = '@' + update.message.from_user.username
    if args:
        for username2 in args:
            debts_manager.delete(username, username2)
        update.message.reply_text('Deleted')
    else:
        update.message.reply_text('No username specified')


def start_command(update: telegram.Update, context: telegram.ext.CallbackContext):
    args = context.args
    update.message.reply_text(static.start_message)


def help_command(update: telegram.Update, context: telegram.ext.CallbackContext):
    args = context.args
    update.message.reply_text(static.help_message, parse_mode='html')


def error_callback(update: telegram.Update, context: telegram.ext.CallbackContext):
    args = context.args
    error = context.error
    update.message.reply_text(f'[ERROR]:\n{str(error)}')
    print(str(error))


def queryHandler(update: telegram.Update, context: telegram.ext.CallbackContext):
    query = update.callback_query.data
    message = update.callback_query.message
    update.callback_query.answer()
    context.bot.delete_message(chat_id=message.chat_id, message_id=message.message_id)


if __name__ == '__main__':
    TOKEN = os.environ.get('TOKEN')
    MODE = os.environ.get('MODE', "")
    URL = os.environ.get('URL')
    PORT = os.environ.get('PORT', 80)
    DATABASE_URL = os.environ.get('DATABASE_URL')
    DEBUG = bool(os.environ.get('DEBUG'))

    debts_manager = DebtsManager(DATABASE_URL, DEBUG)
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('split', split_command, pass_args=True))
    dispatcher.add_handler(CommandHandler('lend', lend_command, pass_args=True))
    dispatcher.add_handler(CallbackQueryHandler(queryHandler))
    dispatcher.add_handler(CommandHandler('history', history_command, pass_args=True))
    dispatcher.add_handler(CommandHandler('status', status_command))
    dispatcher.add_handler(CommandHandler('delete', delete_command, pass_args=True))
    dispatcher.add_handler(CommandHandler('start', start_command))
    dispatcher.add_handler(CommandHandler('help', help_command))
    dispatcher.add_error_handler(error_callback)

    if MODE.lower() == 'webhook':
        updater.start_webhook(listen='0.0.0.0', port=int(PORT), url_path=TOKEN)
        updater.bot.setWebhook(URL + '/' + TOKEN)
        updater.idle()
    elif MODE.lower() == 'polling':
        updater.start_polling()
        updater.idle()
    else:
        print(f'[ERROR] MODE should either "WEBHOOK", either "polling". MODE "{MODE}" is not supported.')

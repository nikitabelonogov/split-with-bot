import logging
import os
from telegram.ext import Updater, CommandHandler

import static
from DebtsManager import DebtsManager


def parse_mentions(message):
    result = []
    mentions = [x for x in message['entities'] if x['type'] == 'mention']
    for mention in mentions:
        result.append(message['text'][mention['offset']:mention['offset'] + mention['length']])
    return result


def lend_command(bot, update, args):
    lender = '@' + update.message.from_user.username
    name = args[0]
    total = float(args[1])
    debtors = parse_mentions(update.message)
    response = debts_manager.lend(lender, debtors, name, total, self_except=False)
    update.message.reply_text('\n'.join(map(str, response)) or 'No entries found')


def lend_self_except_command(bot, update, args):
    lender = '@' + update.message.from_user.username
    name = args[0]
    total = float(args[1])
    debtors = parse_mentions(update.message)
    response = debts_manager.lend(lender, debtors, name, total, self_except=True)
    update.message.reply_text('\n'.join(map(str, response)) or 'No entries found')


def history_command(bot, update, args):
    username = '@' + update.message.from_user.username
    if args:
        username2 = args[0]
        response = debts_manager.related_debts(username, username2)
    else:
        response = debts_manager.related_debts(username)
    update.message.reply_text('\n'.join(map(str, response)) or 'No entries found')


def status_command(bot, update, args):
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
            totals[debt.lender] = totals.get(debt.debtor, 0.) - float(debt)
    response = []
    for username, total in totals.items():
        if total < 0:
            response.append('you owes {} {:.0f}₽ in total'.format(username, total))
        elif total > 0:
            response.append('you lent {} {:.0f}₽ in total'.format(username, total))
    update.message.reply_text('\n'.join(map(str, response)) or 'No entries found')


def start_command(bot, update):
    update.message.reply_text(static.start_message)


def help_command(bot, update):
    update.message.reply_text(static.help_message)


def error_callback(bot, update, error):
    try:
        raise error
    except Exception as e:
        logging.exception(str(e))


if __name__ == '__main__':
    TOKEN = os.environ.get('TOKEN')
    MODE = os.environ.get('MODE')
    URL = os.environ.get('URL')
    PORT = os.environ.get('PORT')
    DATABASE_URL = os.environ.get('DATABASE_URL')
    DEBUG = bool(os.environ.get('DEBUG'))

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)

    debts_manager = DebtsManager(DATABASE_URL, DEBUG)
    updater = Updater(TOKEN)

    updater.dispatcher.add_handler(CommandHandler('lend', lend_command, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler('lend_self_except', lend_self_except_command, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler('add', lend_command, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler('add_self_except', lend_self_except_command, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler('history', history_command, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler('status', status_command, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler('start', start_command))
    updater.dispatcher.add_handler(CommandHandler('help', help_command))
    updater.dispatcher.add_error_handler(error_callback)

    if MODE == 'webhook':
        updater.start_webhook(listen='0.0.0.0', port=int(PORT), url_path=TOKEN)
        updater.bot.setWebhook(URL + '/' + TOKEN)
        updater.idle()
    elif MODE == 'polling':
        updater.start_polling()
        updater.idle()

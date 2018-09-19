import os

import datetime
from telegram.ext import Updater, CommandHandler
import logging


def parse_mentions(message):
    result = []
    mentions = [x for x in message['entities'] if x['type'] == 'mention']
    for mention in mentions:
        result.append(message['text'][mention['offset']:mention['offset'] + mention['length']])
    return result


def lend(lender, debtors, name, sum, self_exept=False):
    response = ''
    if not self_exept:
        debtors.append(lender)
    debtors = set(debtors)
    interim_amount = sum / len(debtors)
    for debtor in debtors:
        entry = {'lender': lender,
                 'debtor': debtor,
                 'name': name,
                 'sum': sum,
                 'interim_amount': interim_amount,
                 'date': datetime.datetime.now(), }
        DEBTS.append(entry)
        response += '{} lent {} {:.0f}₽ for {:.0f}₽ {}\n'.format(lender, debtor, interim_amount, sum, name)
    return response


def lend_command(bot, update, args):
    lender = '@' + update.message.from_user.username
    name = args[0]
    sum = int(args[1])
    debtors = parse_mentions(update.message)
    responce = lend(lender, debtors, name, sum, self_exept=False)
    update.message.reply_text(responce)


def lend_self_except_command(bot, update, args):
    lender = '@' + update.message.from_user.username
    name = args[0]
    sum = int(args[1])
    debtors = parse_mentions(update.message)
    responce = lend(lender, debtors, name, sum, self_exept=True)
    update.message.reply_text(responce)


def error_callback(bot, update, error):
    try:
        raise error
    except Exception as e:
        print(e)


if __name__ == '__main__':
    TOKEN = os.environ.get('TOKEN')
    DEBTS = []

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)

    updater = Updater(TOKEN)

    updater.dispatcher.add_handler(CommandHandler('lend', lend_command, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler('lend_self_except', lend_self_except_command, pass_args=True))
    updater.dispatcher.add_error_handler(error_callback)

    updater.start_polling()
    updater.idle()

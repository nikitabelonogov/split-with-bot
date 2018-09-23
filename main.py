import datetime
import logging
import os
import pickle
from telegram.ext import Updater, CommandHandler
import static


class Debt(object):
    def __init__(self, lender, debtor, name, total, interim_amount):
        self.lender = lender
        self.debtor = debtor
        self.name = name
        # TODO: DO NOT STORE MONEY IN FLOAT!
        self.total = float(total)
        self.interim_amount = float(interim_amount)
        self.date = datetime.datetime.now()

    def __str__(self):
        return '{} {} lent {} {:.0f}₽ for {:.0f}₽ {}'.format(
            self.date.date(), self.lender, self.debtor, self.interim_amount, self.total, self.name)

    def __float__(self):
        return self.interim_amount


def parse_mentions(message):
    result = []
    mentions = [x for x in message['entities'] if x['type'] == 'mention']
    for mention in mentions:
        result.append(message['text'][mention['offset']:mention['offset'] + mention['length']])
    return result


def lend(lender, debtors, name, total, self_except=False):
    response = ''
    if not self_except:
        debtors.append(lender)
    debtors = set(debtors)
    interim_amount = total / len(debtors)
    for debtor in debtors:
        debt = Debt(lender, debtor, name, total, interim_amount)
        DEBTS.append(debt)
        if not debt.lender == debt.debtor:
            response += str(debt) + '\n'
    with open('data.pickle', 'wb') as f:
        pickle.dump(DEBTS, f)
    return response


def lend_command(bot, update, args):
    lender = '@' + update.message.from_user.username
    name = args[0]
    total = float(args[1])
    debtors = parse_mentions(update.message)
    response = lend(lender, debtors, name, total, self_except=False)
    update.message.reply_text(response)


def lend_self_except_command(bot, update, args):
    lender = '@' + update.message.from_user.username
    name = args[0]
    total = float(args[1])
    debtors = parse_mentions(update.message)
    response = lend(lender, debtors, name, total, self_except=True)
    update.message.reply_text(response)


def history_command(bot, update, args):
    username = '@' + update.message.from_user.username
    response = ''
    for debt in DEBTS:
        if not debt.lender == debt.debtor:
            if debt.lender == username or debt.debtor == username:
                response += str(debt) + '\n'
    update.message.reply_text(response)


def status_command(bot, update, args):
    response = ''
    username = '@' + update.message.from_user.username
    totals = {}
    for debt in DEBTS:
        if not debt.lender == debt.debtor:
            if debt.lender == username:
                totals[debt.debtor] = totals.get(debt.debtor, 0.) + float(debt)
            elif debt.debtor == username:
                totals[debt.lender] = totals.get(debt.debtor, 0.) - float(debt)
    for username, total in totals.items():
        if total < 0:
            response += 'you owes {} {:.0f}₽ in total\n'.format(username, total)
        elif total > 0:
            response += 'you lent {} {:.0f}₽ in total\n'.format(username, total)
    update.message.reply_text(response)


def help_command(bot, update, args):
    update.message.reply_text(static.help_message)


def error_callback(bot, update, error):
    try:
        raise error
    except Exception as e:
        logging.exception(str(e))


if __name__ == '__main__':
    TOKEN = os.environ.get('TOKEN')
    DEBTS = []
    try:
        with open('data.pickle', 'rb') as f:
            DEBTS = pickle.load(f)
    except Exception as e:
        logging.exception(str(e))

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)

    updater = Updater(TOKEN)

    updater.dispatcher.add_handler(CommandHandler('lend', lend_command, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler('lend_self_except', lend_self_except_command, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler('add', lend_command, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler('add_self_except', lend_self_except_command, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler('history', history_command, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler('status', status_command, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler('help', help_command, pass_args=True))
    updater.dispatcher.add_error_handler(error_callback)

    updater.start_polling()
    updater.idle()

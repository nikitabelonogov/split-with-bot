import datetime
import logging
import os
from sqlalchemy import Column, Integer, String, Float, create_engine, DateTime, or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from telegram.ext import Updater, CommandHandler

import static

Base = declarative_base()
Session = sessionmaker()


class Debt(Base):
    __tablename__ = 'debts'
    id = Column(Integer, primary_key=True)
    lender = Column(String)
    debtor = Column(String)
    name = Column(String)
    total = Column(Float)
    interim_amount = Column(Float)
    datetime = Column(DateTime, default=datetime.datetime.utcnow)

    def __init__(self, lender, debtor, name, total, interim_amount):
        self.lender = lender
        self.debtor = debtor
        self.name = name
        # TODO: DO NOT STORE MONEY IN FLOAT!
        self.total = float(total)
        self.interim_amount = float(interim_amount)

    def __str__(self):
        return '{} {} lent {} {:.0f}₽ for {:.0f}₽ {}'.format(
            self.datetime.date(), self.lender, self.debtor, self.interim_amount, self.total, self.name)

    def __float__(self):
        return self.interim_amount


def parse_mentions(message):
    result = []
    mentions = [x for x in message['entities'] if x['type'] == 'mention']
    for mention in mentions:
        result.append(message['text'][mention['offset']:mention['offset'] + mention['length']])
    return result


def lend(lender, debtors, name, total, self_except=False):
    response = []
    if not self_except:
        debtors.append(lender)
    debtors = set(debtors)
    interim_amount = total / len(debtors)
    session = Session(bind=ENGINE)
    for debtor in debtors:
        debt = Debt(lender, debtor, name, total, interim_amount)
        session.add(debt)
        if not debt.lender == debt.debtor:
            response.append(debt)
    session.commit()
    # TODO: http://docs.sqlalchemy.org/en/latest/errors.html#error-bhk3
    # session.close()
    return response


def lend_command(bot, update, args):
    lender = '@' + update.message.from_user.username
    name = args[0]
    total = float(args[1])
    debtors = parse_mentions(update.message)
    response = lend(lender, debtors, name, total, self_except=False)
    if response:
        update.message.reply_text('\n'.join(map(str, response)))
    else:
        update.message.reply_text('No entries found')


def lend_self_except_command(bot, update, args):
    lender = '@' + update.message.from_user.username
    name = args[0]
    total = float(args[1])
    debtors = parse_mentions(update.message)
    response = lend(lender, debtors, name, total, self_except=True)
    if response:
        update.message.reply_text('\n'.join(map(str, response)))
    else:
        update.message.reply_text('No entries found')


def history_command(bot, update):
    username = '@' + update.message.from_user.username
    session = Session(bind=ENGINE)
    response = session.query(Debt). \
        filter(Debt.lender != Debt.debtor). \
        filter(or_(Debt.lender == username, Debt.debtor == username)). \
        all()
    # TODO: http://docs.sqlalchemy.org/en/latest/errors.html#error-bhk3
    # session.close()
    if response:
        update.message.reply_text('\n'.join(map(str, response)))
    else:
        update.message.reply_text('No entries found')


def status_command(bot, update):
    username = '@' + update.message.from_user.username
    totals = {}
    session = Session(bind=ENGINE)
    for debt in session.query(Debt). \
            filter(Debt.lender != Debt.debtor). \
            filter(or_(Debt.lender == username, Debt.debtor == username)). \
            all():
        if debt.lender == username:
            totals[debt.debtor] = totals.get(debt.debtor, 0.) + float(debt)
        elif debt.debtor == username:
            totals[debt.lender] = totals.get(debt.debtor, 0.) - float(debt)
    # TODO: http://docs.sqlalchemy.org/en/latest/errors.html#error-bhk3
    # session.close()
    response = []
    for username, total in totals.items():
        if total < 0:
            response.append('you owes {} {:.0f}₽ in total'.format(username, total))
        elif total > 0:
            response.append('you lent {} {:.0f}₽ in total'.format(username, total))
    if response:
        update.message.reply_text('\n'.join(map(str, response)))
    else:
        update.message.reply_text('No entries found')


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

    ENGINE = create_engine(DATABASE_URL, echo=DEBUG)

    Base.metadata.create_all(ENGINE)

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)

    updater = Updater(TOKEN)

    updater.dispatcher.add_handler(CommandHandler('lend', lend_command, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler('lend_self_except', lend_self_except_command, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler('add', lend_command, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler('add_self_except', lend_self_except_command, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler('history', history_command))
    updater.dispatcher.add_handler(CommandHandler('status', status_command))
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

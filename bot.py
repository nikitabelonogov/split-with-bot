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


# TODO: integrate logger

def parse_mentions(message) -> list[str]:
    result = []
    mentions = [x for x in message['entities'] if x['type'] == 'mention']
    for mention in mentions:
        result.append(message['text'][mention['offset']:mention['offset'] + mention['length']])
    return result


def split_command(update: telegram.Update, context: telegram.ext.CallbackContext):
    # TODO: Add interactive split
    args = context.args
    lender = '@' + update.message.from_user.username
    name = ' '.join(args)
    for arg in args:
        try:
            total = float(arg)
        except:
            pass
    debtors = parse_mentions(update.message)
    debtors.append(lender)
    debtors = list(set(debtors))
    response = debts_manager.lend(
        lender, debtors, name, total,
        self_except=True,
        group_type=update.effective_chat.type,
        chat_id=update.effective_chat.id,
        message_id=update.effective_message.message_id,
    )
    buttons = [[
        telegram.InlineKeyboardButton("⛔️", callback_data="callback"),
    ]]
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='\n'.join(map(str, response)) or 'No entries found',
        reply_markup=telegram.InlineKeyboardMarkup(buttons),
    )


# TODO: merge lend and split commands
def lend_command(update: telegram.Update, context: telegram.ext.CallbackContext):
    # TODO: Add interactive lend
    print(update)
    print(context)
    args = context.args
    lender = '@' + update.message.from_user.username
    # TODO: Remove mentions from description
    name = ' '.join(args)
    for arg in args:
        try:
            # TODO: parse cents 3.30
            total = float(arg)
        except:
            pass
    debtors = parse_mentions(update.message)
    response = debts_manager.lend(
        lender, debtors, name, total,
        self_except=True,
        group_type=update.effective_chat.type,
        chat_id=update.effective_chat.id,
        message_id=update.effective_message.message_id,
    )

    buttons = [[
        telegram.InlineKeyboardButton("⛔️", callback_data="delete"),
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
        message_text, reply_markup = generate_history_message([username, username2])
    else:
        message_text, reply_markup = generate_history_message([username])
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message_text,
        reply_markup=reply_markup,
        parse_mode='html',
    )


HISTORY_PAGE_SIZE = 10


def generate_history_message(
        usernames: list[str],
        f: int = 0,
        t: int = HISTORY_PAGE_SIZE,
) -> (str, telegram.InlineKeyboardMarkup):
    response = debts_manager.related_debts(usernames)
    result = 'No entries found'
    if response:
        page = response[f:t]
        result = f'<i>history for {", ".join(usernames)}</i>\n'
        result += '\n'.join(map(str, page))
        result += f'<i>\n{str(f)}..{str(t)}/{str(len(response))}</i>'
    buttons_raw = []
    if f > 0:
        buttons_raw.append(
            telegram.InlineKeyboardButton(
                "First Page",
                callback_data=f"history-{str(0)}-{str(10)}"
            )
        )
    if t < len(response):
        buttons_raw.append(
            telegram.InlineKeyboardButton(
                "Next Page",
                callback_data=f"history-{str(f + HISTORY_PAGE_SIZE)}-{str(t + HISTORY_PAGE_SIZE)}"
            )
        )
    buttons = [buttons_raw]

    return result, telegram.InlineKeyboardMarkup(buttons)


def status_command(update: telegram.Update, context: telegram.ext.CallbackContext):
    args = context.args
    username = '@' + update.message.from_user.username
    if args:
        username2 = args[0]
        debts = debts_manager.related_debts([username, username2])
    else:
        debts = debts_manager.related_debts([username])
    totals = {}
    for debt in debts:
        if debt.lender == username:
            totals[debt.debtor] = totals.get(debt.debtor, 0.) + float(debt)
        elif debt.debtor == username:
            totals[debt.lender] = totals.get(debt.lender, 0.) - float(debt)
    response = []
    for username, total in totals.items():
        if total <= -1.:
            response.append('you owes {} {:.0f}{} in total'.format(username, -total, static.currency_char))
        elif total >= 1.:
            response.append('you lent {} {:.0f}{} in total'.format(username, total, static.currency_char))
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

    if query == 'delete':
        context.bot.delete_message(
            chat_id=message.chat_id,
            message_id=message.message_id,
        )
    elif query.startswith('history'):
        username = '@' + update.callback_query.from_user.username
        _, f, t = query.split('-')
        # TODO: use origin user's history
        message_text, reply_markup = generate_history_message([username], f=int(f), t=int(t))
        context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=message.message_id,
            text=message_text,
            reply_markup=reply_markup,
            parse_mode='html',
        )
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f'Unknown query "{query}"',
        )


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
    dispatcher.add_handler(CommandHandler('history', history_command, pass_args=True))
    dispatcher.add_handler(CommandHandler('status', status_command, pass_args=True))
    dispatcher.add_handler(CommandHandler('delete', delete_command, pass_args=True))
    dispatcher.add_handler(CommandHandler('start', start_command))
    dispatcher.add_handler(CommandHandler('help', help_command))
    dispatcher.add_handler(CallbackQueryHandler(queryHandler))
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

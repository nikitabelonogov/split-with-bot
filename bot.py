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

HISTORY_PAGE_SIZE = 10


# TODO: integrate logger

def parse_mentions(message: telegram.Message) -> list[str]:
    result = []
    mentions = [x for x in message['entities'] if x['type'] == 'mention']
    for mention in mentions:
        result.append(message['text'][mention['offset']:mention['offset'] + mention['length']])
    return result


def split_command(update: telegram.Update, context: telegram.ext.CallbackContext):
    lend_command(update, context, split=True)


def lend_command(update: telegram.Update, context: telegram.ext.CallbackContext, split: bool = False):
    # TODO: Add interactive lend
    args = context.args

    if not args:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=static.lend_command_args_missing_message,
            parse_mode='html',
        )
        return

    lender = '@' + update.message.from_user.username
    lenders = [lender]

    total = .0
    for arg in args:
        try:
            # TODO: parse cents 3.30
            total = float(arg)
        except Exception as e:
            print(e)

    debtors = parse_mentions(update.message)
    if split:
        debtors.append(lender)
    debtors = list(set(debtors))
    debt = debts_manager.lend(
        total=total,
        lenders_nicknames=lenders,
        debtors_nicknames=debtors,
        # TODO: Remove mentions from description
        description=' '.join(args),
        group_type=update.effective_chat.type,
        chat_id=update.effective_chat.id,
        message_id=update.effective_message.message_id,
    )

    buttons = [[
        telegram.InlineKeyboardButton(
            static.debt_button_remove_myself_from_debtors_text,
            callback_data=f"remove-from-debt-{str(debt.id)}",
        ),
        telegram.InlineKeyboardButton(
            static.debt_button_add_myself_to_debtors_text,
            callback_data=f"add-to-debt-{str(debt.id)}",
        ),
    ]]
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=debt.telegram_html_message(),
        reply_markup=telegram.InlineKeyboardMarkup(buttons),
    )


def debt_command(update: telegram.Update, context: telegram.ext.CallbackContext):
    args = context.args
    if not args:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=static.debt_command_args_missing_message,
            parse_mode='html',
        )
        return
    debt = debts_manager.getDebtByID(int(args[0]))
    buttons = [[
        telegram.InlineKeyboardButton(
            static.debt_button_remove_myself_from_debtors_text,
            callback_data=f"remove-from-debt-{str(debt.id)}",
        ),
        telegram.InlineKeyboardButton(
            static.debt_button_add_myself_to_debtors_text,
            callback_data=f"add-to-debt-{str(debt.id)}",
        ),
    ]]
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=debt.telegram_html_message(),
        reply_markup=telegram.InlineKeyboardMarkup(buttons),
    )




def history_command(update: telegram.Update, context: telegram.ext.CallbackContext):
    args = context.args
    username = '@' + update.message.from_user.username
    message_text, reply_markup = generate_history_message(username)
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message_text,
        reply_markup=reply_markup,
        parse_mode='html',
    )


def generate_history_message(
        username: str,
        f: int = 0,
        t: int = HISTORY_PAGE_SIZE,
) -> (str, telegram.InlineKeyboardMarkup):
    debts = debts_manager.related_debts(username)
    result = 'No entries found'
    if debts:
        page = debts[f:t]
        result = f'<i>history for {username}</i>\n'
        result += '\n'.join(map(str, page))
        result += f'<i>\n{str(f)}..{str(t)}/{str(len(debts))}</i>'
    buttons_raw = []
    if f > 0:
        buttons_raw.append(
            telegram.InlineKeyboardButton(
                "First Page",
                callback_data=f"history-{str(0)}-{str(10)}"
            )
        )
    if t < len(debts):
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
    totals = {}
    user = debts_manager.get_or_create_user(username)
    debts = debts_manager.related_debts(username)
    for debt in debts:
        for debtor in debt.debtors:
            if user in debt.lenders:
                totals[debtor.nickname] = totals.get(debtor.nickname, 0.) + debt.fraction()
        for lender in debt.lenders:
            if user in debt.debtors:
                totals[lender.nickname] = totals.get(lender.nickname, 0.) - debt.fraction()
    response = []
    for nickname, total in totals.items():
        if total <= -1.:
            response.append(f'{username} owes {nickname} {-total}{static.currency_char} in total')
        elif total >= 1.:
            response.append(f'{username} lent {nickname} {total}{static.currency_char} in total')
    update.message.reply_text('\n'.join(map(str, response)) or 'No entries found')


# def delete_command(update: telegram.Update, context: telegram.ext.CallbackContext):
#     args = context.args
#     username = '@' + update.message.from_user.username
#     if args:
#         for username2 in args:
#             debts_manager.delete(username, username2)
#         update.message.reply_text('Deleted')
#     else:
#         update.message.reply_text('No username specified')


def start_command(update: telegram.Update, context: telegram.ext.CallbackContext):
    args = context.args
    update.message.reply_text(static.start_message, parse_mode='html')


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
    username = '@' + update.callback_query.from_user.username

    if query == 'delete':
        context.bot.delete_message(
            chat_id=message.chat_id,
            message_id=message.message_id,
        )
    elif query.startswith('history'):
        _, f, t = query.split('-')
        # TODO: use origin user's history
        message_text, reply_markup = generate_history_message(username, f=int(f), t=int(t))
        context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=message.message_id,
            text=message_text,
            reply_markup=reply_markup,
            parse_mode='html',
        )
    elif query.startswith('remove-from-debt'):
        debt_id = int(query.split('-')[-1])
        debt = debts_manager.remove_debtor(debt_id, username)
        buttons = [[
            telegram.InlineKeyboardButton(
                static.debt_button_remove_myself_from_debtors_text,
                callback_data=f"remove-from-debt-{str(debt.id)}",
            ),
            telegram.InlineKeyboardButton(
                static.debt_button_add_myself_to_debtors_text,
                callback_data=f"add-to-debt-{str(debt.id)}",
            ),
        ]]
        context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=message.message_id,
            text=debt.telegram_html_message(),
            reply_markup=telegram.InlineKeyboardMarkup(buttons),
            parse_mode='html',
        )
    elif query.startswith('add-to-debt'):
        debt_id = int(query.split('-')[-1])
        debt = debts_manager.add_debtor(debt_id, username)
        buttons = [[
            telegram.InlineKeyboardButton(
                static.debt_button_remove_myself_from_debtors_text,
                callback_data=f"remove-from-debt-{str(debt.id)}",
            ),
            telegram.InlineKeyboardButton(
                static.debt_button_add_myself_to_debtors_text,
                callback_data=f"add-to-debt-{str(debt.id)}",
            ),
        ]]
        context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=message.message_id,
            text=debt.telegram_html_message(),
            reply_markup=telegram.InlineKeyboardMarkup(buttons),
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
    DATABASE_URL = os.environ.get('DATABASE_URL').replace("postgres://", "postgresql://")
    DEBUG = bool(os.environ.get('DEBUG'))

    debts_manager = DebtsManager(DATABASE_URL, DEBUG)
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('split', split_command, pass_args=True))
    dispatcher.add_handler(CommandHandler('lend', lend_command, pass_args=True))
    dispatcher.add_handler(CommandHandler('debt', debt_command, pass_args=True))
    dispatcher.add_handler(CommandHandler('history', history_command, pass_args=True))
    dispatcher.add_handler(CommandHandler('status', status_command, pass_args=True))
    # dispatcher.add_handler(CommandHandler('delete', delete_command, pass_args=True))
    dispatcher.add_handler(CommandHandler('start', start_command))
    dispatcher.add_handler(CommandHandler('help', help_command))
    dispatcher.add_handler(CallbackQueryHandler(queryHandler))
    dispatcher.add_error_handler(error_callback)

    if MODE.lower() == 'webhook':
        updater.start_webhook(listen='0.0.0.0', port=int(PORT), url_path=TOKEN, webhook_url=URL + '/' + TOKEN)
        updater.idle()
    elif MODE.lower() == 'polling':
        updater.start_polling()
        updater.idle()
    else:
        print(f'[ERROR] MODE should either "WEBHOOK", either "polling". MODE "{MODE}" is not supported.')

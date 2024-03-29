import logging
import os

import telegram
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

import static
from DebtsManager import DebtsManager
from Models import User, Debt, round_money

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)

HISTORY_PAGE_SIZE = 10


# TODO: integrate logger

def parse_mentions(message: telegram.Message) -> list[User]:
    result = []
    for entity in message.entities:
        if entity.type == telegram.MessageEntity.MENTION:
            f = entity.offset + 1
            t = entity.offset + entity.length
            username = message.text[f:t]
            user = debts_manager.create_update_user(username=username)
            result.append(user)
        elif entity.type == telegram.MessageEntity.TEXT_MENTION:
            user = debts_manager.create_update_user(
                telegram_id=entity.user.id,
                username=entity.user.username,
                first_name=entity.user.first_name,
                last_name=entity.user.last_name,
                is_bot=entity.user.is_bot,
            )
            result.append(user)
        else:
            pass
    return result


def parse_message(message: telegram.Message) -> (int, str):
    total = 0.
    pure_description = message.text
    for entity in message.entities:
        f = entity.offset
        t = entity.offset + entity.length
        pure_description = pure_description[:f] + ' ' * entity.length + pure_description[t:]
    words = pure_description.split()
    price_index = None
    for index, word in enumerate(words):
        try:
            total = float(word)
            price_index = index
        except Exception as e:
            pass
    words.pop(price_index)
    pure_description = " ".join(words)
    return total, pure_description


def create_update_user(user: telegram.User) -> User:
    return debts_manager.create_update_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        is_bot=user.is_bot,
    )


def split_command(update: telegram.Update, context: telegram.ext.CallbackContext):
    actor = create_update_user(update.effective_message.from_user)
    owe_lend_split_response(update, context, actor, split=True)


def lend_command(update: telegram.Update, context: telegram.ext.CallbackContext):
    actor = create_update_user(update.effective_message.from_user)
    owe_lend_split_response(update, context, actor, split=False)


def owe_command(update: telegram.Update, context: telegram.ext.CallbackContext):
    actor = create_update_user(update.effective_message.from_user)
    owe_lend_split_response(update, context, actor, split=False, owe=True)


def owe_lend_split_response(
        update: telegram.Update,
        context: telegram.ext.CallbackContext,
        actor: User,
        split: bool = False,
        owe: bool = False,
):
    args = context.args

    if not args:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=static.lend_command_args_missing_message,
            parse_mode='html',
        )
        return

    total = .0
    description = ' '.join(args)
    try:
        total, description = parse_message(message=update.effective_message)
    except Exception as e:
        pass

    lenders = [actor]
    debtors = parse_mentions(update.effective_message)
    if split:
        debtors.append(actor)
    debtors = list(set(debtors))
    if owe:
        debtors, lenders = lenders, debtors
    debt = debts_manager.lend(
        total=total,
        lenders=lenders,
        debtors=debtors,
        description=description,
        group_type=update.effective_chat.type,
        chat_id=update.effective_chat.id,
        message_id=update.effective_message.message_id,
    )
    debt_response(update, context, debt)


def debt_response(
        update: telegram.Update,
        context: telegram.ext.CallbackContext,
        debt: Debt,
        edit_message_id: int = None,
):
    buttons = [
        [
            telegram.InlineKeyboardButton(
                static.debt_button_remove_myself_from_debtors_text,
                callback_data=f"remove-from-debt-{str(debt.id)}",
            ),
            telegram.InlineKeyboardButton(
                static.debt_button_add_myself_to_debtors_text,
                callback_data=f"add-to-debt-{str(debt.id)}",
            ),
            telegram.InlineKeyboardButton(
                static.debt_button_remove_debt_text,
                callback_data=f"remove-debt-{str(debt.id)}",
            ),
            telegram.InlineKeyboardButton(
                static.debt_button_check_debt_text,
                callback_data=f"check-debt-{str(debt.id)}",
            ),
        ],
    ]
    if edit_message_id is not None:
        context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=edit_message_id,
            text=debt.telegram_html_message(),
            reply_markup=telegram.InlineKeyboardMarkup(buttons),
            parse_mode='html',
        )
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=debt.telegram_html_message(),
            reply_markup=telegram.InlineKeyboardMarkup(buttons),
            parse_mode='html',
        )


def debt_command(update: telegram.Update, context: telegram.ext.CallbackContext):
    actor = create_update_user(update.effective_message.from_user)
    args = context.args
    if not args:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=static.debt_command_args_missing_message,
            parse_mode='html',
        )
        return
    debt = debts_manager.getDebtByID(int(args[0]))
    debt_response(update, context, debt)


def history_command(update: telegram.Update, context: telegram.ext.CallbackContext):
    actor = create_update_user(update.effective_message.from_user)
    args = context.args
    message_text, reply_markup = generate_history_message(actor)
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message_text,
        reply_markup=reply_markup,
        parse_mode='html',
    )


def generate_history_message(
        actor: User,
        f: int = 0,
        t: int = HISTORY_PAGE_SIZE,
) -> (str, telegram.InlineKeyboardMarkup):
    debts = debts_manager.related_debts(actor)
    result = 'No entries found'
    if debts:
        page = debts[f:t]
        result = f'<i>history for {actor}</i>\n'
        result += '\n'.join(map(str, page))
        result += f'<i>\n{str(f)}..{str(t)}/{str(len(debts))}</i>'
    buttons_raw = []
    if f > 0:
        buttons_raw.append(
            telegram.InlineKeyboardButton(
                "First Page",
                callback_data=f"history-{str(0)}-{str(10)}-{actor.id}"
            )
        )
    if t < len(debts):
        buttons_raw.append(
            telegram.InlineKeyboardButton(
                "Next Page",
                callback_data=f"history-{str(f + HISTORY_PAGE_SIZE)}-{str(t + HISTORY_PAGE_SIZE)}-{actor.id}"
            )
        )
    buttons = [buttons_raw]

    return result, telegram.InlineKeyboardMarkup(buttons)


def status_command(update: telegram.Update, context: telegram.ext.CallbackContext):
    actor = create_update_user(update.effective_message.from_user)
    args = context.args
    totals = {}
    total_total = 0.
    debts = debts_manager.related_debts(actor)
    for debt in debts:
        for debtor in debt.debtors:
            if actor in debt.lenders:
                totals[str(debtor)] = totals.get(str(debtor), 0.) + debt.fraction()
                total_total += debt.fraction()
        for lender in debt.lenders:
            if actor in debt.debtors:
                totals[str(lender)] = totals.get(str(lender), 0.) - debt.fraction()
                total_total -= debt.fraction()
    response = []
    if total_total <= -1.:
        response.append(f'{str(actor)} owes {round_money(-total_total)} in total')
    elif total_total >= 1.:
        response.append(f'{str(actor)} lent {round_money(total_total)} in total')
    for username, total in totals.items():
        if total <= -1.:
            response.append(f'{str(actor)} owes {username} {round_money(-total)} in total')
        elif total >= 1.:
            response.append(f'{str(actor)} lent {username} {round_money(total)} in total')
    update.effective_message.reply_text('\n'.join(map(str, response)) or 'No entries found', parse_mode='html')


def start_command(update: telegram.Update, context: telegram.ext.CallbackContext):
    actor = create_update_user(update.effective_message.from_user)
    args = context.args
    update.effective_message.reply_text(str(actor), parse_mode='html')


def help_command(update: telegram.Update, context: telegram.ext.CallbackContext):
    actor = create_update_user(update.effective_message.from_user)
    args = context.args
    update.effective_message.reply_text(static.help_message, parse_mode='html')


def queryHandler(update: telegram.Update, context: telegram.ext.CallbackContext):
    actor = create_update_user(update.callback_query.from_user)
    query = update.callback_query.data
    message = update.callback_query.message
    update.callback_query.answer()

    if query == 'delete':
        context.bot.delete_message(
            chat_id=message.chat_id,
            message_id=message.message_id,
        )
    elif query.startswith('history'):
        _, f, t, u = query.split('-')
        user = debts_manager.get_user(user_id=u)
        message_text, reply_markup = generate_history_message(user, f=int(f), t=int(t))
        context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=message.message_id,
            text=message_text,
            reply_markup=reply_markup,
            parse_mode='html',
        )
    elif query.startswith('remove-from-debt'):
        debt_id = int(query.split('-')[-1])
        debt = debts_manager.remove_debtor(debt_id, actor)
        debt_response(update, context, debt, edit_message_id=message.message_id)
    elif query.startswith('add-to-debt'):
        debt_id = int(query.split('-')[-1])
        debt = debts_manager.add_debtor(debt_id, actor)
        debt_response(update, context, debt, edit_message_id=message.message_id)
    elif query.startswith('remove-debt-'):
        debt_id = int(query.split('-')[-1])
        debts_manager.remove_debt(debt_id)
        context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=message.message_id,
        )
    elif query.startswith('check-debt-'):
        context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=message.message_id,
            text=message.text,
            parse_mode='html',
        )
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f'Unknown query "{query}"',
        )


def error_callback(update: telegram.Update, context: telegram.ext.CallbackContext):
    args = context.args
    error = context.error
    update.effective_message.reply_text(f'{static.error_message}\n{str(error)}')
    print(str(error))


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
    dispatcher.add_handler(CommandHandler('owe', owe_command, pass_args=True))
    dispatcher.add_handler(CommandHandler('debt', debt_command, pass_args=True))
    dispatcher.add_handler(CommandHandler('history', history_command, pass_args=True))
    dispatcher.add_handler(CommandHandler('status', status_command, pass_args=True))
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

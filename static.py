help_message = \
    """
<code>/start</code> - register yourself
<code>/split</code> [description] [sum] [username...] - lend a split check between users and you
<code>/lend</code> [description] [sum] [username...] - lend a split check between users
<code>/owe</code> [description] [sum] [username...] - owe a split check between users
<code>/history</code>  - show history of debts
<code>/status</code> - show totals
<code>/help</code> - show help message
"""
start_message = \
    """
This telegram bot helps you to split a receipts with your friends.
"""
currency_char = "ლ"
lend_command_args_missing_message = \
    """
args are missing or not correct  😞
example: <code>/lend hookah 700 @test</code>
"""

split_command_args_missing_message = \
    """
args are missing or not correct  😞
example: <code>/split hookah 700 @test</code>
"""

debt_command_args_missing_message = \
    """
args are missing or not correct 😞
example: <code>/debt 1</code>
"""

debt_button_add_myself_to_debtors_text = "Add myself to debtors"
debt_button_remove_myself_from_debtors_text = "Remove myself from debtors"
debt_button_remove_debt_text = "⛔️"
debt_button_check_debt_text = "✅"

error_message = "ERROR! go to https://github.com/nikitabelonogov/split-with-bot and fix it yourself"

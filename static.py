help_message = \
    """
<pre>
<code>/split</code> [description] [sum] [username...] - lend a split check between users and you
<code>/lend</code> [description] [sum] [username...] - lend a split check between users
<code>/history</code>  - show history of debts
<code>/status</code> - show totals
<code>/help</code> - show help message
</pre>
"""
start_message = \
    """
This telegram bot helps you to split a receipts with your friends.
"""
currency_char = "🪙"
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

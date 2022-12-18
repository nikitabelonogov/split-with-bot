from DebtsManager import DebtsManager
from Models import User
import os

if __name__ == '__main__':
    SQLITE_FILE_PATH = 'db-test.sqlite3'
    DATABASE_URL = f'sqlite:///{SQLITE_FILE_PATH}'
    SQL_DEBUG = False

    if os.path.exists(SQLITE_FILE_PATH):
        print(f'Removing {SQLITE_FILE_PATH}')
        os.remove(SQLITE_FILE_PATH)
    debts_manager = DebtsManager(DATABASE_URL, SQL_DEBUG)

    print("Creating user1")
    user1 = debts_manager.create_update_user(
        telegram_id=1,
        first_name='TestUser1',
    )
    for user in debts_manager.session.query(User).all():
        print(f'{user.id} {user.telegram_id} {user.first_name} {user.username} {user}')

    print("Creating user2")
    user2 = debts_manager.create_update_user(
        username="test2",
    )
    for user in debts_manager.session.query(User).all():
        print(f'{user.id} {user.telegram_id} {user.first_name} {user.username} {user}')

    print("Updating user2")
    user3 = debts_manager.create_update_user(
        telegram_id=2,
        first_name='TestUser2',
        username="test2",
    )
    for user in debts_manager.session.query(User).all():
        print(f'{user.id} {user.telegram_id} {user.first_name} {user.username} {user}')

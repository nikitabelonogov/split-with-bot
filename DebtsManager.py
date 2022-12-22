from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from Models import Base, Debt, User

Session = sessionmaker()


def get_or_create(session: Session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        return instance


def get_datetime(x: Debt):
    return x.datetime


class DebtsManager:
    def __init__(self, database_url, debug=False):
        self.engine = create_engine(database_url, echo=debug)
        Base.metadata.create_all(self.engine)
        self.session = Session(bind=self.engine)
        self.session.expire_on_commit = False

    def get_user(self,
                 telegram_id: int = None,
                 username: str = None,
                 user_id: int = None,
                 ) -> User or None:
        if user_id:
            return self.session.query(User).get(user_id)
        if telegram_id:
            return self.session.query(User).filter(User.telegram_id == telegram_id).first()
        if username:
            return self.session.query(User).filter(User.username == username).first()
        return None

    def get_all_users(self) -> list[User]:
        return self.session.query(User).all()

    def create_update_user(self,
                           telegram_id: int = None,
                           first_name: str = None,
                           last_name: str = None,
                           username: str = None,
                           is_bot: bool = False,
                           ) -> User:
        user = None
        if username is not None:
            user = self.get_user(username=username)
        if user is None and telegram_id is not None:
            user = self.get_user(telegram_id=telegram_id)

        if user:
            if telegram_id is not None:
                user.telegram_id = telegram_id
            if first_name is not None:
                user.first_name = first_name
            if last_name is not None:
                user.last_name = last_name
            if username is not None:
                user.username = username
            if is_bot is not None:
                user.is_bot = is_bot
        else:
            user = User(
                telegram_id=telegram_id,
                first_name=first_name,
                last_name=last_name,
                username=username,
                is_bot=is_bot
            )
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def lend(
            self,
            total: float,
            description: str = '',
            lenders: list[User] = None,
            debtors: list[User] = None,
            group_type: str = None,
            chat_id: str = None,
            message_id: str = None,
    ) -> Debt:
        debt = Debt(
            total=total,
            description=description,
            group_type=group_type,
            chat_id=chat_id,
            message_id=message_id,
        )

        debt.add_debtors(debtors)
        debt.add_lenders(lenders)

        self.session.add(debt)
        self.session.commit()
        self.session.refresh(debt)
        return debt

    def related_debts(self, user: User) -> list[Debt]:
        self.session.refresh(user)
        return sorted(list(set(user.debts + user.lends)), key=get_datetime, reverse=True)

    def getDebtByID(self, debt_id: int) -> Debt:
        return self.session.query(Debt).get(debt_id)

    def add_debtor(self, debt_id: int, user: User) -> Debt:
        debt = self.getDebtByID(debt_id)
        self.session.add(user)
        debt.add_debtors([user])
        self.session.add(debt)
        self.session.commit()
        self.session.refresh(debt)
        return debt

    def remove_debtor(self, debt_id: int, user: User) -> Debt:
        debt = self.getDebtByID(debt_id)
        self.session.add(user)
        debt.remove_debtors([user])
        self.session.add(debt)
        self.session.commit()
        self.session.refresh(debt)
        return debt

    def remove_debt(self, debt_id: int):
        debt = self.getDebtByID(debt_id)
        print(debt)
        self.session.delete(debt)
        self.session.commit()

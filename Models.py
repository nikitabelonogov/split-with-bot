import datetime
from typing import Any

from sqlalchemy import Integer, Column, String, Float, DateTime, Boolean, Table, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

import static

DEBT_TABLE_NAME = 'debt'
USER_TABLE_NAME = 'user'

Base = declarative_base()

debtors_association_table = Table(
    "debtors_association_table",
    Base.metadata,
    Column(DEBT_TABLE_NAME, ForeignKey(f"{DEBT_TABLE_NAME}.id"), primary_key=True),
    Column(USER_TABLE_NAME, ForeignKey(f"{USER_TABLE_NAME}.id"), primary_key=True),
)

lenders_association_table = Table(
    "lenders_association_table",
    Base.metadata,
    Column(DEBT_TABLE_NAME, ForeignKey(f"{DEBT_TABLE_NAME}.id"), primary_key=True),
    Column(USER_TABLE_NAME, ForeignKey(f"{USER_TABLE_NAME}.id"), primary_key=True),
)


def round_money(amount: float, currency_symbol: str = static.currency_char) -> str:
    return "{:,.2f}{}".format(amount, currency_symbol)


class User(Base):
    __tablename__ = USER_TABLE_NAME
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=True)
    username = Column(String, unique=True, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    is_bot = Column(Boolean, default=False)
    custom_name = Column(String, nullable=True)
    lends = relationship("Debt", secondary=lenders_association_table, back_populates="lenders")
    debts = relationship("Debt", secondary=debtors_association_table, back_populates="debtors")

    def __init__(
            self,
            telegram_id: int = None,
            first_name: str = None,
            last_name: str = None,
            username: str = None,
            is_bot: bool = False,
            *args: Any,
            **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.telegram_id = telegram_id
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.is_bot = bool(is_bot)

    def __str__(self) -> str:
        return self.telegram_html_message()

    def fullname(self) -> str:
        if self.custom_name is not None:
            if len(self.custom_name) == 1:
                return f'@{str(self.custom_name)}'
            return str(self.custom_name)
        if self.last_name is not None:
            return f'{self.first_name} {self.last_name}'
        return f'{self.first_name}'

    def telegram_html_message(self) -> str:
        if self.telegram_id is not None:
            return f'<a href="tg://user?id={self.telegram_id}">{self.fullname()}</a>'
        if self.username is not None:
            return f'@{self.username}'
        return '???'


def mentions(users: list[User]) -> str:
    return ', '.join([str(u) for u in users])


class Debt(Base):
    __tablename__ = DEBT_TABLE_NAME
    id = Column(Integer, primary_key=True)
    lenders = relationship("User", secondary=lenders_association_table, back_populates="lends")
    debtors = relationship("User", secondary=debtors_association_table, back_populates="debts")
    description = Column(String)
    # TODO: DO NOT STORE MONEY IN FLOAT!
    total = Column(Float)
    active = Column(Boolean, default=True)
    datetime = Column(DateTime, default=datetime.datetime.utcnow)
    group_type = Column(String)
    chat_id = Column(String)
    message_id = Column(String)

    def __init__(
            self,
            total: float,
            description: str = '',
            lenders: list[User] = None,
            debtors: list[User] = None,
            group_type: str = None,
            chat_id: str = None,
            message_id: str = None,
            active: bool = True,
            *args: Any,
            **kwargs: Any
    ):
        super().__init__(*args, **kwargs)
        self.add_lenders(lenders)
        self.add_debtors(debtors)
        self.description = description
        self.total = total
        self.group_type = group_type
        self.chat_id = str(chat_id)
        self.message_id = message_id
        self.active = active

    def __str__(self):
        return self.telegram_html_message()

    def add_lenders(self, lenders: list[User] = None):
        if lenders:
            for lender in lenders:
                self.lenders.append(lender)

    def add_debtors(self, debtors: list[User] = None):
        if debtors:
            for debtor in debtors:
                if debtor not in self.debtors:
                    self.debtors.append(debtor)

    def remove_debtors(self, debtors: list[User] = None):
        if debtors:
            for debtor in debtors:
                if debtor in self.debtors:
                    self.debtors.remove(debtor)

    def date_with_link_html(self) -> str:
        raw_date = str(self.datetime.date())
        if self.chat_id and self.message_id and self.group_type == 'supergroup':
            return f'<a href="https://t.me/c/{self.chat_id[4:]}/{self.message_id}">{raw_date}</a>'
        else:
            return raw_date

    def total_formated(self) -> str:
        return round_money(self.total)

    def debtors_formated(self) -> str:
        if len(self.debtors) == 1:
            return f'to {mentions(self.debtors)}'
        if len(self.debtors) > 1:
            return f'split between: {mentions(self.debtors)} ({round_money(self.fraction())})'
        return 'no debtors'

    def description_formated(self) -> str:
        if self.description:
            return f'"{self.description}"'
        return 'no description'

    def telegram_html_message(self) -> str:
        return " ".join(map(str, [
            self.date_with_link_html(),
            self.id,
            mentions(self.lenders),
            self.description_formated(),
            self.total_formated(),
            self.debtors_formated(),
        ]))

    def fraction(self) -> float:
        if len(self.lenders) == 0 or len(self.debtors) == 0:
            return 0.
        return self.total / len(self.debtors) / len(self.lenders)

    def __float__(self):
        return self.total

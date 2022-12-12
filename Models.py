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


class User(Base):
    __tablename__ = USER_TABLE_NAME
    id = Column(Integer, primary_key=True)
    nickname = Column(String)

    def __init__(
            self, nickname,
            *args: Any,
            **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.nickname = nickname

    def __str__(self) -> str:
        return self.nickname


def mentions(users: list[User]) -> str:
    return ', '.join([u.nickname for u in users])


class Debt(Base):
    __tablename__ = DEBT_TABLE_NAME
    id = Column(Integer, primary_key=True)
    lenders = relationship("User", secondary=lenders_association_table)
    debtors = relationship("User", secondary=debtors_association_table)
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
        self.chat_id = chat_id
        self.message_id = message_id
        self.active = active

    def __str__(self):
        return '{} {} lent {} {:.0f}{} for {:.0f}{} {}'.format(
            self.date_with_link_html(),
            self.lender,
            self.debtor,
            self.interim_amount,
            static.currency_char,
            self.total,
            static.currency_char,
            self.name,
        )

    def add_lenders(self, lenders: list[User] = None):
        if lenders:
            for lender in lenders:
                self.lenders.append(lender)

    def add_debtors(self, debtors: list[User] = None):
        if debtors:
            for debtor in debtors:
                self.debtors.append(debtor)


    def date_with_link_html(self) -> str:
        raw_date = str(self.datetime.date())
        if self.chat_id and self.message_id and self.group_type == 'supergroup':
            return f'<a href="https://t.me/c/{self.chat_id[4:]}/{self.message_id}">{raw_date}</a>'
        else:
            return raw_date

    def telegram_html_message(self) -> str:
        split_amount = self.total / len(self.debtors)
        lines = []
        lines.append(f'{self.date_with_link_html()} {mentions(self.lenders)} {self.description} {self.total}{static.currency_char}')
        lines.append(f'split between: {mentions(self.debtors)} ({split_amount}{static.currency_char})')
        return '\n'.join(lines)
    def __float__(self):
        return self.total
import datetime
from typing import Any

from sqlalchemy import Integer, Column, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base

import static

Base = declarative_base()


class Debt(Base):
    __tablename__ = 'debts'
    id = Column(Integer, primary_key=True)
    lender = Column(String)
    debtor = Column(String)
    name = Column(String)
    # TODO: DO NOT STORE MONEY IN FLOAT!
    total = Column(Float)
    interim_amount = Column(Float)
    active = Column(Boolean, default=True)
    datetime = Column(DateTime, default=datetime.datetime.utcnow)
    group_type = Column(String)
    chat_id = Column(String)
    message_id = Column(String)

    def __init__(
            self,
            lender: str,
            debtor: str,
            name: str,
            total: float,
            interim_amount: float,
            group_type: str = None,
            chat_id: str = None,
            message_id: str = None,
            *args: Any,
            **kwargs: Any
    ):
        super().__init__(*args, **kwargs)
        self.lender = lender
        self.debtor = debtor
        self.name = name
        self.total = float(total)
        self.interim_amount = float(interim_amount)
        self.group_type = group_type
        self.chat_id = chat_id
        self.message_id = message_id

    def __str__(self):
        if self.chat_id and self.message_id and self.group_type == 'supergroup':
            return '<a href="https://t.me/c/{}/{}">{}</a> {} lent {} {:.0f}{} for {:.0f}{} {}'.format(
                self.chat_id[4:],
                self.message_id,
                self.datetime.date(),
                self.lender,
                self.debtor,
                self.interim_amount,
                static.currency_char,
                self.total,
                static.currency_char,
                self.name,
            )
        else:
            return '{} {} lent {} {:.0f}{} for {:.0f}{} {}'.format(
                self.datetime.date(),
                self.lender,
                self.debtor,
                self.interim_amount,
                static.currency_char,
                self.total,
                static.currency_char,
                self.name,
            )

    def __float__(self):
        return self.interim_amount

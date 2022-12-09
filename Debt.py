import datetime
from sqlalchemy import Integer, Column, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base

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

    def __init__(self, lender, debtor, name, total, interim_amount, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.lender = lender
        self.debtor = debtor
        self.name = name
        self.total = float(total)
        self.interim_amount = float(interim_amount)

    def __str__(self):
        return '{} {} lent {} {:.0f}₽ for {:.0f}₽ {}'.format(
            self.datetime.date(), self.lender, self.debtor, self.interim_amount, self.total, self.name)

    def __float__(self):
        return self.interim_amount

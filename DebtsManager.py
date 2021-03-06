from sqlalchemy import create_engine, or_, and_
from sqlalchemy.orm import sessionmaker

from Debt import Base, Debt

Session = sessionmaker()


class DebtsManager:
    def __init__(self, database_url, debug=False):
        self.engine = create_engine(database_url, echo=debug)
        Base.metadata.create_all(self.engine)

    def lend(self, lender, debtors, name, total, self_except=False):
        result = []
        if not self_except:
            debtors.append(lender)
        debtors = set(debtors)
        interim_amount = total / len(debtors) if len(debtors) else total
        session = Session(bind=self.engine)
        for debtor in debtors:
            debt = Debt(lender, debtor, name, total, interim_amount)
            session.add(debt)
            if not debt.lender == debt.debtor:
                result.append(debt)
        session.commit()
        # TODO: http://docs.sqlalchemy.org/en/latest/errors.html#error-bhk3
        # session.close()
        return result

    def related_debts(self, username1, username2=None):
        session = Session(bind=self.engine)
        if username2:
            return session.query(Debt). \
                filter(Debt.lender != Debt.debtor). \
                filter(Debt.active). \
                filter(or_(and_(Debt.lender == username1, Debt.debtor == username2),
                           and_(Debt.lender == username2, Debt.debtor == username1))). \
                all()
        else:
            return session.query(Debt). \
                filter(Debt.lender != Debt.debtor). \
                filter(Debt.active). \
                filter(or_(Debt.lender == username1, Debt.debtor == username1)). \
                all()

    def delete(self, username1, username2=None):
        session = Session(bind=self.engine)
        if username2:
            session.query(Debt). \
                filter(Debt.lender != Debt.debtor). \
                filter(Debt.active). \
                filter(or_(and_(Debt.lender == username1, Debt.debtor == username2),
                           and_(Debt.lender == username2, Debt.debtor == username1))). \
                delete(synchronize_session='fetch')
        else:
            session.query(Debt). \
                filter(Debt.lender != Debt.debtor). \
                filter(Debt.active). \
                filter(or_(Debt.lender == username1, Debt.debtor == username1)). \
                delete(synchronize_session='fetch')
        session.commit()

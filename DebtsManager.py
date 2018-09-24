from sqlalchemy import create_engine, or_
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
        interim_amount = total / len(debtors)
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

    def related_debts(self, username):
        session = Session(bind=self.engine)
        return session.query(Debt). \
            filter(Debt.lender != Debt.debtor). \
            filter(or_(Debt.lender == username, Debt.debtor == username)). \
            all()
        # TODO: http://docs.sqlalchemy.org/en/latest/errors.html#error-bhk3
        # session.close()

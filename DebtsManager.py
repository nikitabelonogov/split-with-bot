from sqlalchemy import create_engine, or_, and_
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


class DebtsManager:
    def __init__(self, database_url, debug=False):
        self.engine = create_engine(database_url, echo=debug)
        Base.metadata.create_all(self.engine)
        self.session = Session(bind=self.engine)
        self.session.expire_on_commit = False

    def get_or_create_user(self, nickname: str) -> User:
        return get_or_create(self.session, User, nickname=nickname)

    def lend(
            self,
            total: float,
            description: str = '',
            lenders_nicknames: list[str] = None,
            debtors_nicknames: list[str] = None,
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

        for lender_nickname in lenders_nicknames:
            debt.lenders.append(self.get_or_create_user(lender_nickname))

        for debtor_nickname in debtors_nicknames:
            debt.debtors.append(self.get_or_create_user(debtor_nickname))

        self.session.add(debt)
        self.session.commit()
        return self.getDebtByID(debt.id)

    def related_debts(self, username: str) -> list[Debt]:
        user = self.get_or_create_user(username)
        return list(set(user.debts + user.lends))

    # def delete(self, username1, username2=None):
    #     session = Session(bind=self.engine)
    #     if username2:
    #         session.query(Debt). \
    #             filter(Debt.lender != Debt.debtor). \
    #             filter(Debt.active). \
    #             filter(or_(and_(Debt.lender == username1, Debt.debtor == username2),
    #                        and_(Debt.lender == username2, Debt.debtor == username1))). \
    #             delete(synchronize_session='fetch')
    #     else:
    #         session.query(Debt). \
    #             filter(Debt.lender != Debt.debtor). \
    #             filter(Debt.active). \
    #             filter(or_(Debt.lender == username1, Debt.debtor == username1)). \
    #             delete(synchronize_session='fetch')
    #     session.commit()

    def getDebtByID(self, debt_id: int) -> Debt:
        return self.session.query(Debt).get(debt_id)

    def add_debtor(self, debt_id: int, username: str) -> Debt:
        debt = self.getDebtByID(debt_id)
        user = self.get_or_create_user(username)
        self.session.add(user)
        debt.add_debtors([user])
        self.session.add(debt)
        self.session.commit()
        return self.getDebtByID(debt.id)

    def remove_debtor(self, debt_id: int, username: str) -> Debt:
        debt = self.getDebtByID(debt_id)
        user = self.get_or_create_user(username)
        self.session.add(user)
        debt.remove_debtors([user])
        self.session.add(debt)
        self.session.commit()
        return self.getDebtByID(debt.id)

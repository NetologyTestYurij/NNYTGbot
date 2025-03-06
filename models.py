"""Модели для работы с базой данных"""

from typing import Annotated
import sqlalchemy as sq
from sqlalchemy import BigInteger, ForeignKey, String, text, CheckConstraint
from sqlalchemy.orm import declarative_base, DeclarativeBase, Mapped, mapped_column, relationship

from typing import Annotated

from sqlalchemy import BigInteger, ForeignKey, String, text, CheckConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# Анотация типов для подстановки в модели таблиц
int_pk = Annotated[int, mapped_column(primary_key=True)]
str_40 = Annotated[str, 40]


class Base(DeclarativeBase):
    """Базовый класс для всех моделей"""
    type_annotation_map = {
        str_40: String(40)
    }


class User(Base):
    """Модель таблицы app_user"""
    __tablename__ = 'app_user'
    user_id: Mapped[int_pk]
    telegram_id: Mapped[int] = mapped_column(BigInteger())

    card: Mapped['Card'] = relationship(back_populates='user', cascade='all, delete')


class WordGroup(Base):
    """Модель таблицы word_group"""
    __tablename__ = 'word_group'
    group_id: Mapped[int_pk]
    alias: Mapped[str_40]

    card: Mapped['Card'] = relationship(back_populates='group', cascade='all, delete')


class Card(Base):
    """Модель таблицы card"""
    __tablename__ = 'card'
    card_id: Mapped[int_pk]
    user_id: Mapped[int] = mapped_column(ForeignKey('app_user.user_id'))
    ru_word: Mapped[str_40]
    en_word: Mapped[str_40]
    custom: Mapped[bool] = mapped_column(server_default=text('FALSE'))
    group_id: Mapped[int | None] = mapped_column(ForeignKey('word_group.group_id'))
    success_rate: Mapped[int] = mapped_column(server_default=text('0'))
    failure_rate: Mapped[int] = mapped_column(server_default=text('0'))

    user: Mapped['User'] = relationship(back_populates='card', cascade='all, delete')
    group: Mapped['WordGroup'] = relationship(back_populates='card', cascade='all, delete')

    __table_args__ = (
        CheckConstraint("success_rate >= 0", name="check_success_rate_positive"),
        CheckConstraint("failure_rate >= 0", name="check_failure_rate_positive")

    )



def create_tables(engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    
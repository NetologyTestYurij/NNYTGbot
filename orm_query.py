"""Модуль содержит функции для взаимодействия с базой данных"""
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.functions import random
from default_data import card_data, group_data
from models import User, Card, WordGroup, create_tables
from random import randrange
from sqlalchemy.ext.asyncio import AsyncSession

DSN = "postgresql://postgres:REWQ5432@localhost:5432/netology_db"
engine = sqlalchemy.create_engine(DSN)

create_tables(engine)

Session = sessionmaker(bind=engine)
session = Session()

def add_user(session: AsyncSession, tg_id: int):
    """
    Функция добавляет нового пользователя в таблицу 'app_user'
   
    """
    user = User(
        telegram_id=tg_id
    )

    session.add(user)
    session.commit()


def get_random_word(session: AsyncSession, cnt: int):
    """
    Функция возвращает указанное количество случайных слов из базы данных
    
    """
    en_word_list = []
    ru_word_list = []
    query = select(Card).order_by(random()).limit(cnt)
    result = session.execute(query)

    for row in result.scalars().all():
        en_word_list.append(row.en_word)
        ru_word_list.append(row.ru_word)

    return en_word_list, ru_word_list


def check_word(session: AsyncSession, word: str):
    """
    Проверка выбранного пользователем слова на корректность
    
    """
    query = select(Card.en_word).where(Card.ru_word == word)
    result = session.execute(query)
    return result.scalars().all()[0]


def check_added_word(session: AsyncSession, word: str):
    """
    Функция проверяет наличие указанного слова в базе данных
    
    """
    query = select(Card.ru_word).where(Card.ru_word == word)
    result = session.execute(query)
    return result.scalar_one_or_none()


def add_group(session: AsyncSession, data: dict):
    """
    Добавляет новую группу в базу данных

    """
    for row in data:
        group = WordGroup(
            alias=row['alias']
        )
        session.add(group)

    session.commit()


async def add_card(session: AsyncSession, tg_id: int, word: str, word_en: str ):
    """
    Добавляет новое слово в базу данных
    
    """
    #yd = YandexDict()
    query = select(User.user_id).where(User.telegram_id == tg_id)
    result = session.execute(query)
    user = result.scalars().all()[0]

    card = Card(
        user_id=user,
        ru_word=word,
        en_word=word_en,
        custom=True,
        group_id=5
    )

    session.add(card)
    session.commit()


def delete_card(session: AsyncSession, word: int):
    """
    Удаляет пользовательское слово из базы данных
    
    """
    query = delete(Card).where(Card.en_word == word)
    session.execute(query)
    session.commit()


def get_all_card(session: AsyncSession, tg_id: int):
    """
    Возвращает список всех пользовательских слов
    
    """
    subq = select(User.user_id).where(User.telegram_id == tg_id).subquery('get_tg_id')
    query = select(Card).where(and_( Card.user_id == subq, Card.custom == True))
    words_dict = {}
    result =  session.execute(query)

    for row in result.scalars().all():
        words_dict[row.ru_word] = row.en_word

    words_dict['Отменить удаление'] = 'cancel'

    return words_dict


def update_word_success_rate(session: AsyncSession, word: str):
    """
    Обновляет количество правильных ответов для слова
   
    """
    update_query = select(Card).filter_by(ru_word = word)
    result = session.execute(update_query)
    updating_word = result.scalar_one()
    updating_word.success_rate += 1
    session.commit()


def update_word_failure_rate(session: AsyncSession, word: str):
    """
    Обновляет количество неправильных ответов для слова
    """
    update_query = select(Card).filter_by(ru_word = word)
    result = session.execute(update_query)
    updating_word = result.scalar_one()
    updating_word.failure_rate += 1
    session.commit()


def default_word(session: AsyncSession, data: dict, tg_id: int):
    """
    Функция добавляет изначальные данные для слов в базу данных
    
    """
    query = select(User.user_id).where(User.telegram_id == tg_id)
    result = session.execute(query)
    user = result.scalars().all()[0]

    for row in data:
        card = Card(
            user_id=user,
            #user_id = tg_id,#потом удалить
            ru_word=row['ru_word'],
            en_word=row['en_word'],
            group_id=row['group_id']
        )
        session.add(card)

    session.commit()

#add_user(session, 3333)
#default_word(session, card_data, 3333)
"""
q = session.query(WordGroup)
for row in q:
    print(row.alias, row.group_id)


w = session.query(Card)
for ro in w:
    print(ro.card_id, ro.en_word, ro.ru_word)
#print(get_random_word())
"""

session.close()
#

import telebot
import random
import sqlalchemy
from sqlalchemy import select
from random import randrange
from telebot import types, State
from telebot.handler_backends import State, StatesGroup
from models import Card
from default_data import card_data, group_data
from orm_query import get_random_word, default_word, check_word, add_group, add_user, session, add_card#, orm_add_card

#print('Start telegram bot...')
TOKEN = ""
bot = telebot.TeleBot(TOKEN)
known_users = []
userStep = {}
buttons = []

#add_user(bot.user.id)
#add_default_word(bot.user.id)

#print(bot.user.id)

def show_hint(*lines):
    return '\n'.join(lines)

def show_target(data):
    return f"{data['target_word']} -> {data['translate_word']}"

class Command:
    ADD_WORD = 'Добавить слово ➕'
    DELETE_WORD = 'Удалить слово🔙'
    NEXT = 'Дальше ⏭'

class MyStates(StatesGroup):
    target_word = State()
    translate_word = State()
    another_words = State()
    adding_new_word = State()
    saving_new_word = State()
    deleting_word = State()

def get_user_step(uid):
    if uid in userStep:
        return userStep[uid]
    else:
        known_users.append(uid)
        userStep[uid] = 0
        print("New user detected, who hasn't used \"/start\" yet")
        return 0

@bot.message_handler(commands=['cards','start'])
def create_cards(message):
    add_user(session, message.from_user.id)
    add_group(session, group_data)
    default_word(session, card_data, message.from_user.id)
    #тут запоминаем id
    cid = message.chat.id
    if cid not in known_users:
        known_users.append(cid)
        userStep[cid] = 0
        bot.send_message(cid, "Hello")
    markup = types.ReplyKeyboardMarkup(row_width=2)
    en_words, ru_words = get_random_word(session, 4)
    russian_word = ru_words[randrange(4)]
    global buttons
    buttons = []
    target_word =  check_word(session, russian_word)# брать из БД
    translate = russian_word  # брать из БД
    others = en_words # брать из БД
    other_words_btns = [types.KeyboardButton(word) for word in others]
    buttons.extend(other_words_btns)
    random.shuffle(buttons)
    next_btn = types.KeyboardButton(Command.NEXT)
    add_word_btn = types.KeyboardButton(Command.ADD_WORD)
    delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
    buttons.extend([next_btn, add_word_btn, delete_word_btn])

    markup.add(*buttons)

    greeting = f"Выбери перевод слова:\n🇷🇺 {translate}"
    bot.send_message(message.chat.id, greeting, reply_markup=markup)
    bot.set_state(message.from_user.id, MyStates.target_word, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['target_word'] = target_word
        data['translate_word'] = translate
        data['other_words'] = others
   


@bot.message_handler(func=lambda message: message.text == Command.NEXT)
def next_cards(message):
    create_cards(message)


@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def delete_word(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        print(data['target_word'])  # удалить из БД


@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
def add_word(message):
    cid = message.chat.id
    bot.set_state(user_id=message.from_user.id, chat_id=cid, state=MyStates.adding_new_word)
    bot.send_message(cid, "Введите слово, которое вы хотите добавить, на английском:")
    print(message.text)  # сохранить в БД

#@bot.message_handler(func=lambda message: get_user_step(message.chat.id) == 1)
@bot.message_handler(state=MyStates.adding_new_word)
def add_translate_word(message):
    cid = message.chat.id
    word = message.text.strip().capitalize()

    # Проверяем, что слова нет в общем словаре
    if check_word(word):
        bot.send_message(cid, "Это слово уже есть в общем словаре. Пожалуйста, введите другое слово.")
        return

    # Сохраняем слово в состоянии
    with bot.retrieve_data(user_id=message.from_user.id, chat_id=cid) as data:
        data['target_word'] = word

    bot.set_state(user_id=message.from_user.id, chat_id=cid, state=MyStates.saving_new_word)
    bot.send_message(cid, f"Теперь введите перевод для слова '{word}':")

@bot.message_handler(state=MyStates.saving_new_word)
def save_new_word(message):
    cid = message.chat.id
    translation = message.text.strip().capitalize()

    # Проверяем, что перевод не пустой
    if not translation:
        bot.send_message(cid, "Перевод не может быть пустым. Пожалуйста, введите перевод.")
        return

    try:
        # Извлекаем данные из состояния
        with bot.retrieve_data(user_id=message.from_user.id, chat_id=cid) as data:
            target_word = data.get('target_word').capitalize()

        if not target_word:
            bot.send_message(cid, "Ошибка! Попробуй снова начать с /start.")
            bot.delete_state(user_id=message.from_user.id, chat_id=cid)
            return

        # Сохраняем новое слово в персональный словарь пользователя
        add_card(session, message.from_user.id, target_word, translation)

        bot.send_message(cid, f"Слово '{target_word}' и его перевод '{translation}' успешно добавлены!")
    except Exception as e:
        print(f"Произошла ошибка при сохранении слова: {e}")
        bot.send_message(cid, f"Произошла ошибка при сохранении слова: {e}")
    finally:
        bot.delete_state(user_id=message.from_user.id, chat_id=cid)

@bot.message_handler(func=lambda message: True, content_types=['text'])
def message_reply(message):
    print("333")
    text = message.text
    markup = types.ReplyKeyboardMarkup(row_width=2)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        target_word = data['target_word']

        if text == target_word:
            hint = show_target(data)
            hint_text = ["Отлично!❤", hint]
            hint = show_hint(*hint_text)
        else:
            for btn in buttons:
                if btn.text == text:
                    btn.text = text + '❌'
                    break
            hint = show_hint("Допущена ошибка!",
                             f"Попробуй ещё раз вспомнить слово 🇷🇺{data['translate_word']}")
    markup.add(*buttons)
    bot.send_message(message.chat.id, hint, reply_markup=markup)

if __name__ == '__main__':
    print('Bot is running')
    bot.polling()

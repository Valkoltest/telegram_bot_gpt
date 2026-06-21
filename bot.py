from http.client import responses

from pip._internal.commands import download
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CallbackQueryHandler, CommandHandler, ContextTypes
from gpt import ChatGptService
from util import (load_message, send_text, send_image, show_main_menu,
                  default_callback_handler, load_prompt, send_text_buttons, Dialog)

import credentials

import random

import os


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dialog.mode = "DEFAULT"
    text = load_message('main')
    await send_image(update, context, 'main')
    await send_text(update, context, text)
    await show_main_menu(update, context, {
        'start': 'Головне меню',
        'random': 'Дізнатися випадковий цікавий факт 🧠',
        'gpt': 'Задати питання чату GPT 🤖',
        'talk': 'Поговорити з відомою особистістю 👤',
        'quiz': 'Взяти участь у квізі ❓',
        'translator': 'Перекладач',
        'voice': 'голосове спілкування з GPT'
        # Додати команду в меню можна так:
        # 'command': 'button text'

    })

# 1. *"Випадковий факт"*
# Телеграм-бот повинен обробляти команду /random.
# При обробці команди він надсилає заздалегідь підготовлене зображення
# та робить запит до ChatGPT із заздалегідь підготовленим промптом.
# Відповідь ChatGPT потрібно отримати та передати користувачеві.
# До повідомлення має бути прикріплена кнопка "Закінчити", натискання на яку
# працює так само, як команда /start.
# І кнопка "Хочу ще факт", натискання на яку
# працює так само, як команда /random


async def bot_random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dialog.mode = "RANDOM"
    await send_image(update, context, 'random')
    prompt = load_prompt('random')
    response = await chat_gpt.send_question(prompt, 'Давай рандомний факт')
    await send_text_buttons(
        update, context,
        response,
        {
            'random_finish' : 'Закінчити',
            'random_one_more' :'Хочу ще факт',
        }
    )
    dialog.mode = "DEFAULT"


async def random_buttons_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query.data
    if query == 'random_finish':
        dialog.mode = "DEFAULT"
        await start(update, context)
    elif query == 'random_one_more':
        await bot_random(update, context)

    await update.callback_query.answer()

# 2. *"ChatGPT інтерфейс"*
# Телеграм-бот повинен обробляти команду /gpt.
# При обробці команди він надсилає заздалегідь підготовлене зображення
# та робить запит до ChatGPT, передаючи йому
# текст отриманого повідомлення. Відповідь ChatGPT потрібно отримати та
# передати користувачеві текстовим повідомленням


async def gpt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dialog.mode = "GPT"
    await send_image(update, context, 'gpt')
    msg = load_message('gpt')
    await send_text(update, context, msg)


async def gpt_dialog(update, context):
    text = update.message.text
    prompt = load_prompt("gpt")
    response = await chat_gpt.send_question(prompt, text)
    await send_text_buttons(
        update, context,
        response,
        {
            'gpt_finish': 'Закінчити',
        }
    )


async def gpt_buttons_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query.data
    if query == 'gpt_finish':
        dialog.mode = None
        await start(update, context)

    await update.callback_query.answer()

# 3. *"Діалог з відомою особистістю"*
# Телеграм-бот повинен обробляти команду /talk.
# При обробці команди бот надсилає заздалегідь підготовлене зображення та
# пропонує вибір з декількох відомих особистостей,
# використовуючи кнопки. При натисканні кнопки потрібно встановити промпт обраної особистості.
# Подальші текстові повідомлення від користувача потрібно передавати ChatGPT та
# повертати його відповіді користувачеві.
# До них має бути прикріплена кнопка "Закінчити", натискання на яку
# працює так само, як команда /start


async def talk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dialog.mode = "TALK"
    await send_image(update, context, "talk")
    text = load_message('talk')
    lines = text.split('\n')
    await send_text_buttons(update, context, lines[0],
                            {
                                "talk_cobain": "Курт Кобейн - Соліст гурту Nirvana 🎸",
                                "talk_queen": "Єлизавета II - Королева Об'єднаного Королівства 👑",
                                "talk_tolkien": 'Джон Толкін - Автор книги "Володар Перснів" 📖',
                                "talk_nietzsche": "Фрідріх Ніцше - Філософ 🧠",
                                "talk_hawking": "Стівен Гокінг - Фізик 🔬"
                            }
                            )


async def talk_buttons_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query.data
    dialog.mode = query
    await person(update, context, query)

    await update.callback_query.answer()


async def person(update: Update, context: ContextTypes.DEFAULT_TYPE, name: str):
    await send_image(update, context, name)


async def person_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE, name: str):
    text = update.message.text
    prompt = load_prompt(name)
    response = await chat_gpt.send_question(prompt, text)
    await send_text(update, context, response)

#4. *"Квіз"*
# Телеграм-бот повинен обробляти команду /quiz.
# При обробці команди бот надсилає заздалегідь підготовлене зображення
# та пропонує вибір з декількох тем, використовуючи кнопки.
# Після вибору теми, передати запит ChatGPT і, отримавши питання квізу, передати його
# користувачеві. Наступне текстове повідомлення користувача вважається відповіддю.
# Його потрібно передати ChatGPT та отримати результат. Результат передати користувачеві
# з можливістю задати ще питання на ту ж тему, змінити тему або закінчити квіз, за допомогою кнопок.
# Бот також повинен вести рахунок правильних відповідей та
# відображати разом з черговим результатом

quiz_themes = {
            "quiz_prog": "Програмування",
            "quiz_math": "Математика",
            "quiz_biology": "Біологія",
            "quiz_more": "Одна з попередніх тем",
        }


async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dialog.mode = "QUIZ"
    await send_image(update, context, "quiz")
    text = load_message("quiz")
    await send_text_buttons(
        update,
        context,
        text,
        quiz_themes
    )


async def quiz_buttons_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query.data
    quiz_theme = query
    prompt = load_prompt("quiz")
    chat_gpt.set_prompt(prompt)
    dialog.mode = quiz_theme
    dialog.success = 0
    dialog.question_counter = 0
    await quiz_gpt_question(update, context, quiz_theme)

    await update.callback_query.answer()


async def quiz_gpt_question(update: Update, context: ContextTypes.DEFAULT_TYPE, theme: str):
    dialog.question_counter += 1
    if theme == "quiz_more":
        theme = list(quiz_themes.keys())[random.randint(0, 3)]
    response = await chat_gpt.add_message(theme)
    await send_text(update, context, response)
    dialog.asked_question = True


async def quiz_gpt_answer(update:Update, context: ContextTypes.DEFAULT_TYPE):
    if dialog.asked_question:
        answer = update.message.text
        response = await chat_gpt.add_message(answer)
        if response == "Правильно!":
            dialog.success += 1
        text = f"{response} \nУспіх: {dialog.success} з {dialog.question_counter}"
        await send_text_buttons(update, context, text,
                                {
                                    "theme_continue": "Наступне питання",
                                    "theme_choice": "Змінити тему",
                                    "theme_end": "Закічити квіз",
                                }
                                )
        dialog.asked_question = False
    else:
        await send_text(update, context, "Ви на це питання вже відповіли. Оберіть команду.")


async def theme_buttons_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query.data
    if query == "theme_continue":
        await quiz_gpt_question(update, context, dialog.mode)
    elif query == "theme_choice":
        await quiz(update, context)
    elif query == "theme_end":
        await start(update, context)

# **"Перекладач"**#
# Бот пропонує вибрати мову, на яку потрібно перекласти текст, використовуючи кнопки.
# Після вибору мови користувач надсилає текст, який потрібно перекласти.
# Бот використовує ChatGPT для перекладу тексту та надсилає результат користувачеві.
# До повідомлення має бути прикріплена кнопка зміни мови та кнопка "Закінчити", натискання на яку
# працює так само, як команда /start.


async def translator(update: Update, context: ContextTypes.DEFAULT_TYPE):
        dialog.mode = "TRANSLATOR"
        await send_image(update, context, 'translator')
        text = load_message("translator")
        lines = text.split("\n")
        await send_text_buttons(update, context, lines[0],
                                {
                                    'trans_ua': '🇺🇦 Українська',
                                    'trans_en': '🇬🇧 Англійська',
                                    'trans_fr': '🇫🇷 Фрацузська',
                                    'trans_es': '🇪🇸 Іспанська',
                                    'trans_de': '🇩🇪 Німецька'
                                })


async def translator_buttons_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query.data
    dialog.mode = query
    prompt = load_prompt("translator")
    chat_gpt.set_prompt(prompt)
    await translator_gpt_invitation(update, context, query)

    await update.callback_query.answer()


async def translator_gpt_invitation(update: Update, context: ContextTypes.DEFAULT_TYPE, language: str):
    response = await chat_gpt.add_message(language)
    await send_text(update, context, response)


async def translator_gpt_answer(update: Update, context: ContextTypes.DEFAULT_TYPE, language: str):
    text = update.message.text
    response = await chat_gpt.add_message(text)
    await send_text_buttons(update, context, response,
                            {
                                "lang_change": "Змінити мову",
                                "lang_end": "Закінчити"
                            })


async def language_buttons_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query.data
    if query == "lang_change":
        await translator(update, context)
    elif query == "lang_end":
        await start(update, context)


# **"Голосовий ChatGPT"**
# Бот повинен прийняти голосове повідомлення від користувача. Перевести його в текст
# та надіслати ChatGPT. Отримавши відповідь, перетворити її на голосове повідомлення та
# надіслати у вигляді аудіоповідомлення користувачеві.


async def voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dialog.mode = 'voice'
    await send_image(update, context, 'voice')
    text = load_message('voice')
    await send_text(update, context, text)
    prompt = load_prompt('voice')
    chat_gpt.set_prompt(prompt)

async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    path = "resources/voice/voice_in.oga"
    file = await update.message.voice.get_file()
    await file.download_to_drive(path)
    response_from_voice = await chat_gpt.send_voice(path)
    text = response_from_voice.text
    response = await chat_gpt.add_message(text)
    await send_text(update, context, response)






async def menu_text_handler(update, context):
    if dialog.mode == "DEFAULT":
        await send_text(update, context, "Використовуйте доступні комнди.")
    elif dialog.mode == "GPT":
        await gpt_dialog(update, context)
    elif dialog.mode == "TALK":
        await talk(update, context)
    elif dialog.mode[:5] == "talk_":
        await person_dialog(update, context, dialog.mode)
    elif dialog.mode[:5] == "quiz_":
        await quiz_gpt_answer(update, context)
    elif dialog.mode[:6] == "trans_":
        await translator_gpt_answer(update, context, dialog.mode)
    else:
        await send_text(update, context, "Використовуйте доступні комнди.")

#
dialog = Dialog()
dialog.mode = None
dialog.success = 0
dialog.question_counter = 0
dialog.asked_question = False

chat_gpt = ChatGptService(credentials.ChatGPT_TOKEN)
app = ApplicationBuilder().token(credentials.BOT_TOKEN).build()

# Зареєструвати обробник команди можна так:
app.add_handler(CommandHandler('start', start))
app.add_handler(CommandHandler('random', bot_random))
app.add_handler(CommandHandler('gpt', gpt))
app.add_handler(CommandHandler('talk', talk))
app.add_handler(CommandHandler('quiz', quiz))
app.add_handler(CommandHandler('translator', translator))
app.add_handler(CommandHandler('voice', voice))

# Зареєструвати обробник колбеку можна так:
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_text_handler))
app.add_handler(CallbackQueryHandler(random_buttons_handler, pattern='^random_.*'))
app.add_handler(CallbackQueryHandler(gpt_buttons_handler, pattern='^gpt_.*'))
app.add_handler(CallbackQueryHandler(talk_buttons_handler, pattern='^talk_.*'))
app.add_handler(CallbackQueryHandler(quiz_buttons_handler, pattern='^quiz_.*'))
app.add_handler(CallbackQueryHandler(theme_buttons_handler, pattern='^theme_.*'))
app.add_handler(CallbackQueryHandler(translator_buttons_handler, pattern='^trans_.*'))
app.add_handler(CallbackQueryHandler(language_buttons_handler, pattern='^lang_.*'))
app.add_handler(MessageHandler(filters.VOICE, voice_handler))
# app.add_handler(CallbackQueryHandler(default_callback_handler))
app.run_polling()
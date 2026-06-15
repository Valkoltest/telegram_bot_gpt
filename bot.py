from http.client import responses

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CallbackQueryHandler, CommandHandler, ContextTypes
from gpt import ChatGptService
from util import (load_message, send_text, send_image, show_main_menu,
                  default_callback_handler, load_prompt, send_text_buttons, Dialog)

import credentials

import random

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dialog.mode = None
    text = load_message('main')
    await send_image(update, context, 'main')
    await send_text(update, context, text)
    await show_main_menu(update, context, {
        'start': 'Головне меню',
        'random': 'Дізнатися випадковий цікавий факт 🧠',
        'gpt': 'Задати питання чату GPT 🤖',
        'talk': 'Поговорити з відомою особистістю 👤',
        'quiz': 'Взяти участь у квізі ❓'
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
    dialog.mode = "random"
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
    dialog.mode = None
async def random_buttons_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query.data
    if query == 'random_finish':
        dialog.mode = None
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
    dialog.mode = "gpt"
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
    dialog.mode = talk
    await send_image(update, context, "talk")
    text = load_message('talk')
    lines = text.split('\n')
    await send_text_buttons(update, context, lines[0],
                            {
                                "person_1": lines[3],
                                "person_2": lines[4],
                                "person_3": lines[5],
                                "person_4": lines[6],
                                "person_5": lines[7],
                            }
                    )

person_data = ["talk_cobain", "talk_queen", "talk_tolkien", "talk_nietzsche", "talk_hawking"]

async def talk_buttons_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query.data
    if query == "person_1":
        dialog.mode = "person_1"
        await person(update, context, 0)
    elif query == "person_2":
        dialog.mode = "person_2"
        await person(update, context, 1)
    elif query == "person_3":
        dialog.mode = "person_3"
        await person(update, context, 2)
    elif query == "person_4":
        dialog.mode = "person_4"
        await person(update, context, 3)
    elif query == "person_5":
        dialog.mode = "person_5"
        await person(update, context, 4)

    await update.callback_query.answer()

async def person(update: Update, context: ContextTypes.DEFAULT_TYPE, index: int):
    await send_image(update, context, person_data[index])

async def person_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE, index: int):
    text = update.message.text
    prompt = load_prompt(person_data[index])
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
    await send_image(update, context, "quiz")
    text = load_message("quiz")
    await send_text_buttons(
        update,
        context,
        text,
        quiz_themes
    )
async def quiz_buttons_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    quiz_theme = ""
    query = update.callback_query.data
    if query == "quiz_prog":
        quiz_theme = list(quiz_themes.keys())[0]
    elif query == "quiz_math":
        quiz_theme = list(quiz_themes.keys())[1]
    elif query == "quiz_biology":
        quiz_theme = list(quiz_themes.keys())[2]
    elif query == "quiz_more":
        quiz_theme = list(quiz_themes.keys())[3]
    dialog.mode = quiz_theme
    dialog.success = 0
    dialog.question_counter = 0
    await quiz_gpt_question(update, context, quiz_theme)

    await update.callback_query.answer()

async def quiz_gpt_question(update: Update, context: ContextTypes.DEFAULT_TYPE, theme: str):
    dialog.question_counter += 1
    prompt = load_prompt("quiz")
    if theme == "quiz_more":
        theme = list(quiz_themes.keys())[random.randint(0, 3)]
    response = await chat_gpt.send_question(prompt, theme)
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

async def menu_text_handler(update, context):
    if dialog.mode == "gpt":
        await gpt_dialog(update, context)
    elif dialog.mode == "talk":
        await talk(update, context)
    elif dialog.mode == "person_1":
        await person_dialog(update, context, 0)
    elif dialog.mode == "person_2":
        await person_dialog(update, context, 1)
    elif dialog.mode == "person_3":
        await person_dialog(update, context, 2)
    elif dialog.mode == "person_4":
        await person_dialog(update, context, 3)
    elif dialog.mode == "person_5":
        await person_dialog(update, context, 4)
    elif dialog.mode == "quiz_prog":
        await quiz_gpt_answer(update, context)
    elif dialog.mode == "quiz_math":
        await quiz_gpt_answer(update, context)
    elif dialog.mode == "quiz_biology":
        await quiz_gpt_answer(update, context)
    elif dialog.mode == "quiz_more":
        await quiz_gpt_answer(update, context)
    else:
        await send_text(update, context, "Використовуйте доступні комнди.")


#
dialog = Dialog()
dialog.mode = None
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

# Зареєструвати обробник колбеку можна так:
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_text_handler))
app.add_handler(CallbackQueryHandler(random_buttons_handler, pattern='^random_.*'))
app.add_handler(CallbackQueryHandler(gpt_buttons_handler, pattern='^gpt_.*'))
app.add_handler(CallbackQueryHandler(talk_buttons_handler, pattern='^person_.*'))
app.add_handler(CallbackQueryHandler(quiz_buttons_handler, pattern='^quiz_.*'))
app.add_handler(CallbackQueryHandler(theme_buttons_handler, pattern='^theme_.*'))
# app.add_handler(CallbackQueryHandler(default_callback_handler))
app.run_polling()
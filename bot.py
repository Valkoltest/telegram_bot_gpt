from http.client import responses

from telegram import Update
#from telegram.ext import ApplicationBuilder, CallbackQueryHandler, ContextTypes, CommandHandler, filters
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CallbackQueryHandler, CommandHandler, ContextTypes
#from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from gpt import ChatGptService
from util import (load_message, send_text, send_image, show_main_menu,
                  default_callback_handler, load_prompt, send_text_buttons, Dialog)

import credentials

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

async def random(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        await random(update, context)

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
    dialog.mode = None
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
        await person1(update, context)
    elif query == "person_2":
        dialog.mode = "person_2"
        await person2(update, context)
    elif query == "person_3":
        dialog.mode = "person_3"
        await person3(update, context)
    elif query == "person_4":
        dialog.mode = "person_4"
        await person4(update, context)
    elif query == "person_5":
        dialog.mode = "person_5"
        await person5(update, context)



async def person1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_image(update, context, person_data[0])

async def person2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_image(update, context, person_data[1])

async def person3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_image(update, context, person_data[2])

async def person4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_image(update, context, person_data[3])

async def person5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_image(update, context, person_data[4])

async def person1_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    prompt = load_prompt(person_data[0])
    response = await chat_gpt.send_question(prompt, text)
    await send_text(update, context, response)

async def person2_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    prompt = load_prompt(person_data[1])
    response = await chat_gpt.send_question(prompt, text)
    await send_text(update, context, response)

async def person3_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    prompt = load_prompt(person_data[2])
    response = await chat_gpt.send_question(prompt, text)
    await send_text(update, context, response)

async def person4_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    prompt = load_prompt(person_data[3])
    response = await chat_gpt.send_question(prompt, text)
    await send_text(update, context, response)

async def person5_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    prompt = load_prompt(person_data[4])
    response = await chat_gpt.send_question(prompt, text)
    await send_text(update, context, response)

async def menu_text_handler(update, context):
    if dialog.mode == "gpt":
        await gpt_dialog(update, context)
    elif dialog.mode == "random":
        await random(update, context)
    elif dialog.mode == "talk":
        await talk(update, context)
    elif dialog.mode == "person_1":
        await person1_dialog(update, context)
    elif dialog.mode == "person_2":
        await person2_dialog(update, context)
    elif dialog.mode == "person_3":
        await person3_dialog(update, context)
    elif dialog.mode == "person_4":
        await person4_dialog(update, context)
    elif dialog.mode == "person_5":
        await person5_dialog(update, context)

#
dialog = Dialog()
dialog.mode = None

chat_gpt = ChatGptService(credentials.ChatGPT_TOKEN)
app = ApplicationBuilder().token(credentials.BOT_TOKEN).build()

# Зареєструвати обробник команди можна так:
app.add_handler(CommandHandler('start', start))
app.add_handler(CommandHandler('random', random))
app.add_handler(CommandHandler('gpt', gpt))
app.add_handler(CommandHandler('talk', talk))

# Зареєструвати обробник колбеку можна так:
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_text_handler))
app.add_handler(CallbackQueryHandler(random_buttons_handler, pattern='^random_.*'))
app.add_handler(CallbackQueryHandler(gpt_buttons_handler, pattern='^gpt_.*'))
app.add_handler(CallbackQueryHandler(talk_buttons_handler, pattern='^person_.*'))
# app.add_handler(CallbackQueryHandler(default_callback_handler))
app.run_polling()
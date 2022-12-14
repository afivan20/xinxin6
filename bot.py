from dotenv import dotenv_values
from telegram import Update, Chat
from telegram.ext import CommandHandler, ApplicationBuilder, ContextTypes


from web_apis import fetch_lingo_data, fetch_qkid_data
from extract_data import extract_data_lingoace, extract_data_qkid
from sort import quickort
from util import async_timed


import asyncio
import logging
from datetime import datetime, timedelta, timezone, time
from zoneinfo import ZoneInfo
import pathlib
import os
import time as t


logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s", datefmt='%b-%d-%Y %H:%M:%S %p', level=logging.INFO
)
logger = logging.getLogger('bot.py')


DIR = pathlib.Path(__file__).parent.resolve()
env = dotenv_values(os.path.join(DIR, '.env'))
token = env['TOKEN']


application = ApplicationBuilder().token(token).build()


async def wake_up(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    await context.bot.send_message(chat_id=chat.id,
                             text="today's schedule click 👉 /today \ntomorrow's schedule click 👉 /tomorrow \nthis week 👉 /week \nnext week 👉 /next_week")

def output(data: list) -> str:
    if len(data) == 0:
        return '<b>FREE TIME! ❤️ </b>'
    result = ''
    weekday = ''
    for lesson in data:
        start = lesson['start']
        end = lesson['end']
        utc_start = datetime.utcfromtimestamp(start).replace(tzinfo=timezone.utc)
        utc_end = datetime.utcfromtimestamp(end).replace(tzinfo=timezone.utc)
        Moscow_start = (utc_start.astimezone(tz=ZoneInfo('Europe/Moscow'))).strftime('<b>%H:%M</b>')
        Moscow_end = (utc_end.astimezone(tz=ZoneInfo('Europe/Moscow'))).strftime('<b>%H:%M</b> %a %d-%m')
        name = lesson['name']

        # визуально разделить по дням недели
        if weekday == '' or weekday != utc_start.strftime('%A'):
            weekday = utc_start.strftime('%A')
            result += f'\n<b>{weekday}</b>\n'+'-'*25+'\n'
        
        result += f'{Moscow_start}-{Moscow_end} {name}\n'


    total=len(data)
    result += f'\n<b>TOTAL: {total}</b>'
    return result

async def runner(lingo_task: asyncio.Task, qkid_task: asyncio.Task, context: ContextTypes.DEFAULT_TYPE, chat: Chat) -> None:
    try:
        lingo = await asyncio.wait_for(lingo_task, timeout=6)
    except asyncio.exceptions.TimeoutError:
        logger.error('Снимаю задачу LingoAce, тайм-аут')
        lingo = None
    try:
        qkid = await asyncio.wait_for(qkid_task, timeout=3)
    except asyncio.exceptions.TimeoutError:
        logger.exception('Снимаю задачу QK, тайм-аут')
        qkid = None

    
    
    if not lingo is None:
        try:
            lingo = extract_data_lingoace(lingo)
        except Exception as e:
            logger.exception(f"{e}\nlingo={repr(lingo)}", exc_info=True)
            await context.bot.send_message(chat_id=chat.id, parse_mode ='HTML', text=f'Can not read data from <b>LingoAce</b>.')
            lingo = []
    else:
        await context.bot.send_message(chat_id=chat.id, parse_mode ='HTML', text=f'Can not read data from <b>LingoAce</b>.')
        lingo = []

    if not qkid is None:
        try:
            qkid = extract_data_qkid(qkid)
        except Exception as e:
            logger.exception(f"{e}\nqkid={repr(qkid)}", exc_info=True)
            await context.bot.send_message(chat_id=chat.id, parse_mode ='HTML', text=f'Can not read data from <b>QKid</b>.')
            qkid = []
    else:
        await context.bot.send_message(chat_id=chat.id, parse_mode ='HTML', text=f'Can not read data from <b>QKid</b>.')
        qkid = []
   

    data = lingo + qkid
    sorted_data = quickort(data)
    message = output(sorted_data)
    await context.bot.send_message(chat_id=chat.id, parse_mode ='HTML', text=message)
     
@async_timed()
async def today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    today_utc = datetime.now(tz=ZoneInfo('Europe/Moscow'))
    begin = datetime.combine(today_utc - timedelta(days=1), time(21, 00, tzinfo=timezone.utc))
    unix_today = int(t.mktime(begin.now(tz=ZoneInfo('Europe/Moscow')).date().timetuple()))


    lingo_task = asyncio.create_task(fetch_lingo_data(begin.strftime('%Y-%m-%dT%H:%M:%S.000Z'), (begin+timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%S.000Z')))
    qkid_task = asyncio.create_task(fetch_qkid_data(unix_today))

    await runner(lingo_task, qkid_task, context, chat)

@async_timed()
async def tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    today_utc = datetime.now(tz=ZoneInfo('Europe/Moscow'))
    begin = datetime.combine(today_utc, time(21, 00, tzinfo=timezone.utc))
    unix_tomorrow = int(t.mktime((today_utc.date() + timedelta(days=1)).timetuple()))

    lingo_task = asyncio.create_task(fetch_lingo_data(begin.strftime('%Y-%m-%dT%H:%M:%S.000Z'), (begin+timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%S.000Z')))
    qkid_task = asyncio.create_task(fetch_qkid_data(unix_tomorrow))

    await runner(lingo_task, qkid_task, context, chat)



@async_timed()
async def week(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    today_utc = datetime.now(tz=ZoneInfo('Europe/Moscow'))
    since_monday = (today_utc - timedelta(days=(today_utc.weekday()+1))).date()
    begin = datetime.combine(since_monday, time(21, 00, tzinfo=timezone.utc))
    from_monday = (today_utc - timedelta(days=today_utc.weekday())).date()
    unix_week = int(t.mktime(from_monday.timetuple()))

    lingo_task = asyncio.create_task(fetch_lingo_data(begin.strftime('%Y-%m-%dT%H:%M:%S.000Z'), (begin+timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%S.000Z')))
    qkid_task = asyncio.create_task(fetch_qkid_data(unix_week, week=True))

    await runner(lingo_task, qkid_task, context, chat)

@async_timed()
async def next_week(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    today_utc = datetime.now(tz=ZoneInfo('Europe/Moscow'))
    next_monday = ((today_utc - timedelta(days=(today_utc.weekday()+1))) + timedelta(days=7)).date()
    begin = datetime.combine(next_monday, time(21, 00, tzinfo=timezone.utc))
    unix_next_week = int(t.mktime((next_monday).timetuple()))

    lingo_task = asyncio.create_task(fetch_lingo_data(begin.strftime('%Y-%m-%dT%H:%M:%S.000Z'), (begin+timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%S.000Z')))
    qkid_task = asyncio.create_task(fetch_qkid_data(unix_next_week, week=True))

    await runner(lingo_task, qkid_task, context, chat)






start_handler = CommandHandler('start', wake_up)
today_handler = CommandHandler('today', today, block=False)
tomorrow_handler = CommandHandler('tomorrow', tomorrow, block=False)
week_handler = CommandHandler('week', week, block=False)
next_week_handler = CommandHandler('next_week', next_week, block=False)



if __name__ == '__main__':
    application.add_handler(start_handler)
    application.add_handler(today_handler)
    application.add_handler(tomorrow_handler)
    application.add_handler(week_handler)
    application.add_handler(next_week_handler)
    application.run_polling()

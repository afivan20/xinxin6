from dotenv import dotenv_values
from telegram.ext import Updater, CommandHandler

from lingoace_api import extract_data_lingoace
from qkid_api import extract_data_qkid
from datetime import datetime, timedelta
from sort import quickort
import pathlib
import os
import time as t

DIR = pathlib.Path(__file__).parent.resolve()
env = dotenv_values(os.path.join(DIR, '.env'))
token = env['TOKEN']


updater = Updater(token=token)




def wake_up(update, context):
    chat = update.effective_chat
    context.bot.send_message(chat_id=chat.id,
                             text="today's schedule click 👉 /today \ntomorrow's schedule click 👉 /tomorrow \nthis week 👉 /week \nnext week 👉 /next_week")

def output(data):
    if len(data) == 0:
        return '<b>FREE TIME! ❤️ </b>'
    result = ''
    weekday = ''
    for lesson in data:
        start = lesson['start']
        end = lesson['end']
        utc_start = datetime.utcfromtimestamp(start)
        utc_end = datetime.utcfromtimestamp(end)
        Moscow_start = (utc_start + timedelta(hours=3)).strftime('<b>%H:%M</b>')
        Moscow_end = (utc_end + timedelta(hours=3)).strftime('<b>%H:%M</b> %a %d-%m')
        name = lesson['name']

        # визуально разделить по дням недели
        if weekday == '' or weekday != utc_start.strftime('%A'):
            weekday = utc_start.strftime('%A')
            result += f'\n<b>{weekday}</b>\n'+'-'*25+'\n'
        
        result += f'{Moscow_start}-{Moscow_end} {name}\n'


    total=len(data)
    result += f'\n<b>TOTAL: {total}</b>'
    return result



def today(update, context):
    chat = update.effective_chat
    today = datetime.utcnow().today()
    since_monday = (today - timedelta(days=(today.weekday()+1))).date()
    try:
        lingo = extract_data_lingoace(since_monday, today)
    except Exception as e:
        context.bot.send_message(chat_id=chat.id, parse_mode ='HTML', text=f'No data from LingoAce. Error: {e}\n\n <b>Plz, try again later...</b>')
        lingo = []

    unix_today = int(t.mktime(today.date().timetuple()))
    try:
        qkid = extract_data_qkid(from_day=unix_today)
    except Exception as e:
        context.bot.send_message(chat_id=chat.id, parse_mode ='HTML', text=f'No data from QKid. Error: {e}\n\n <b>Plz, try again later...</b>')
        qkid = []

    try:
        data = lingo + qkid
        sorted_data = quickort(data)
    except Exception as e:
        context.bot.send_message(chat_id=chat.id, parse_mode ='HTML', text=f'Cannot extract data: {e}\n\n <b>Plz, try again later...</b>')
        return
    message = output(sorted_data)

    context.bot.send_message(chat_id=chat.id, parse_mode ='HTML', text=message)


def tomorrow(update, context):
    chat = update.effective_chat
    today = datetime.utcnow().today()
    since_monday = (today - timedelta(days=(today.weekday()+1))).date()
    tomorrow = today + timedelta(days=1) # что если завтра Понедельник, а значит новая неделя
    if tomorrow.weekday() == 0:
        since_monday = today.date()
    try:
        lingo = extract_data_lingoace(since=since_monday, day=tomorrow)
    except Exception as e:
        context.bot.send_message(chat_id=chat.id, parse_mode ='HTML', text=f'No data from LingoAce. Error: {e}\n\n <b>Plz, try again later...</b>')
        lingo = []
    
    unix_tomorrow = int(t.mktime((today.date() + timedelta(days=1)).timetuple()))
    try:
        qkid = extract_data_qkid(from_day=unix_tomorrow)
    except Exception as e:
        context.bot.send_message(chat_id=chat.id, parse_mode ='HTML', text=f'No data from QKid. Error: {e}\n\n <b>Plz, try again later...</b>')
        qkid = []

    try:
        data = lingo + qkid
        sorted_data = quickort(data)
    except Exception as e:
        context.bot.send_message(chat_id=chat.id, parse_mode ='HTML', text=f'Cannot extract data: {e}\n\n <b>Plz, try again later...</b>')
        return
    message = output(sorted_data)

    context.bot.send_message(chat_id=chat.id, parse_mode ='HTML', text=message)


def week(update, context):
    chat = update.effective_chat

    today = datetime.utcnow().today()
    since_monday = (today - timedelta(days=(today.weekday()+1))).date()
    try:
        lingo = extract_data_lingoace(since=since_monday, day=today, week=True)
    except Exception as e:
        context.bot.send_message(chat_id=chat.id, parse_mode ='HTML', text=f'No data from LingoAce. Error: {e}\n\n <b>Plz, try again later...</b>')
        lingo = []
    
    from_monday = (today - timedelta(days=today.weekday())).date()
    unix_week = int(t.mktime(from_monday.timetuple()))
    try:
        qkid = extract_data_qkid(from_day=unix_week, is_week=True)
    except Exception as e:
        context.bot.send_message(chat_id=chat.id, parse_mode ='HTML', text=f'No data from QKid. Error: {e}\n\n <b>Plz, try again later...</b>')
        qkid = []
    
    try:
        data = lingo + qkid
        sorted_data = quickort(data)
    except Exception as e:
        context.bot.send_message(chat_id=chat.id, parse_mode ='HTML', text=f'Cannot extract data: {e}\n\n <b>Plz, try again later...</b>')
        return
    message = output(sorted_data)

    context.bot.send_message(chat_id=chat.id, parse_mode ='HTML', text=message)







def next_week(update, context):
    chat = update.effective_chat
    today = datetime.utcnow().today()
    next_monday = ((today - timedelta(days=(today.weekday()+1))) + timedelta(days=7)).date()
    try:
        lingo = extract_data_lingoace(since=next_monday, day=today, week=True)
    except Exception as e:
        context.bot.send_message(chat_id=chat.id, parse_mode ='HTML', text=f'No data from LingoAce. Error: {e}\n\n <b>Plz, try again later...</b>')
        lingo = []
    
    from_monday = (today - timedelta(days=(today.weekday()))).date()
    unix_next_week = int(t.mktime((from_monday + timedelta(days=7)).timetuple()))

    try:
        qkid = extract_data_qkid(from_day=unix_next_week, is_week=True)
    except Exception as e:
        context.bot.send_message(chat_id=chat.id, parse_mode ='HTML', text=f'No data from QKid. Error: {e}\n\n <b>Plz, try again later...</b>')
        qkid = []
    
    try:
        data = lingo + qkid
        sorted_data = quickort(data)
    except Exception as e:
        context.bot.send_message(chat_id=chat.id, parse_mode ='HTML', text=f'Cannot extract data: {e}\n\n <b>Plz, try again later...</b>')
        return
    message = output(sorted_data)

    context.bot.send_message(chat_id=chat.id, parse_mode ='HTML', text=message)





updater.dispatcher.add_handler(CommandHandler('start', wake_up))
updater.dispatcher.add_handler(CommandHandler('today', today))
updater.dispatcher.add_handler(CommandHandler('tomorrow', tomorrow))
updater.dispatcher.add_handler(CommandHandler('week', week))
updater.dispatcher.add_handler(CommandHandler('next_week', next_week))


if __name__ == '__main__':
    updater.start_polling()
    updater.idle()


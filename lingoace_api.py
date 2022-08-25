from dotenv import dotenv_values
from datetime import timedelta
import requests
import pathlib
import os
import time as t
from datetime import datetime, timedelta


DIR = pathlib.Path(__file__).parent.resolve()
env = dotenv_values(os.path.join(DIR, '.env'))
login = env['login']
hash = env['hash']
password = env['password']
role = env['role']
tutor_id = env['tutor_id']


def get_token():
    url = 'https://teacher.lingo-ace.com/api/user/login'
    payload = {
        'identify': login,
        'password': hash,
        'plainPassword': password,
        'role': role
    }
    try:
        token = requests.post(url, json=payload)
        data = token.json()
        token = data['data']['jwtToken']
    except Exception as e:
        print(f'Нет токена Lingoace {e}') # добавить в логгер
        return False

    return token


def lessons(monday):
    token=get_token()
    if token == False:
        return False
    id = tutor_id
    start = f'{monday}T21:00:00.000Z'
    sunday = monday + timedelta(days=7)
    end = f'{sunday}T21:00:00.000Z'
    url = f'https://teacher.lingo-ace.com/api/schedule/tutor/timetable/publish/{id}/{start}/{end}'
    try:
        response = requests.get(url, headers={'authorization': f'Bearer {token}'})
        data = response.json()
        result = data['data']['tutorTimetableList']
    except Exception as e:
        print(f'Упс, нет данных от lingoace {e}') # добавить в логгер
        return False
    return result


def extract_data_lingoace(since, day, week=False):
    result = []
    data_lingoace = lessons(since)
    for lesson in data_lingoace:
        if str(day.date()) == lesson['startTime'][:10] or week==True:
            start_utc = lesson['startTime']
            end_utc = lesson['endTime']

            dt_start = datetime.strptime(start_utc, '%Y-%m-%dT%H:%M:00.000Z')
            dt_end = datetime.strptime(end_utc, '%Y-%m-%dT%H:%M:00.000Z')
            unix_start = int(t.mktime(dt_start.timetuple()) + 10800) # +3 hours 
            unix_end = int(t.mktime(dt_end.timetuple()) + 10800) # +3 hours 

            name = lesson['studentUsername']
            data = {'start':unix_start, 'end':unix_end, 'name': name}
            result.append(data)
    return result
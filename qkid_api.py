import requests
from dotenv import dotenv_values
import pathlib
import os

DIR = pathlib.Path(__file__).parent.resolve()
env = dotenv_values(os.path.join(DIR, '.env'))
version = env['version']
qk_password = env['qk_password']
qk_username = env['qk_username']


def get_token():
    url = 'https://gate.97kid.com/t/user/login'
    payload = {
        "installationJsVersion": version,
        "password": qk_password,
        "username": qk_username
    }
    response = requests.post(url, json=payload)
    # Опасное место, иногда приходит пустой ответ raise JSONDecodeError("Expecting value", s, err.value) from None
    try:
        data = response.json()
        token = data['access_token']
    except Exception as e:
        print(f'Не получилось получить токен Qkid {e}') # можно использовать предущие токены (время жизни 10 часов)
        return False
    return token



def qkid_lessons(from_day, week = False):
    token=get_token()
    if token == False:
        return False
    if week:
        start = from_day
        end = start + (86400*7)
    else:
        start = from_day
        end = start + 86400
    url = f'https://gate.97kid.com/t/calendars/my?beginAt={start}&endAt={end}' 
    headers = {
        'authorization': f'Bearer {token}',
    }
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
    except Exception as e:
        print(f' УПС! нет данных от QKID {e}') # добавить в логгер
        return False

    return data


def extract_data_qkid(from_day, is_week=False):
    data = qkid_lessons(from_day, is_week)
    result = []
    # что если data пришли False, как отличить от пустого списка? []
    for lesson in data:
         if lesson['status'] == 0:
            start = lesson['beginAt']
            end = lesson['endAt']
            level = lesson['params'].get('abbreviation')
            unit = lesson['params'].get('lessonName')
            if level:
                name = f'{level} - {unit}'
            else:
                name = 'Reading class'
            result.append({'start':start, 'end':end, 'name': name})
    return result


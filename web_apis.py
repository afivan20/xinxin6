from dotenv import dotenv_values
import aiohttp

import logging
import pathlib
import os
DIR = pathlib.Path(__file__).parent.resolve()
env = dotenv_values(os.path.join(DIR, '.env'))

TEMP = {'token_lingo': None, 'token_QK': None}


async def get_token_lingo():
    url = 'https://teacher.lingoace.com/api/user/login'
    payload = {
        'identify': env['login'],
        'password': env['hash'],
        'plainPassword': env['password'],
        'role': env['role']
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, ssl=False) as resp:
            token =  await resp.json()
            TEMP['token_lingo'] = token['data']['jwtToken']


async def lingo_data(begin: str, end: str):
    if  not TEMP['token_lingo']:
        await get_token_lingo()

    async with aiohttp.ClientSession() as session:
        url = f"https://teacher.lingo-ace.com/api/schedule/tutor/self/timetable/publish/{env['tutor_id']}/{begin}/{end}/"
        headers = {"authorization": f"Bearer {TEMP['token_lingo']}"}
        try:
            async with session.get(url, ssl=False, headers=headers) as resp:
                data = await resp.json()
            if data['code'] == 200:
                return data['data']
            else:
                logging.info("Couldn't get the LingoAce data. Start again")
                TEMP['token_lingo'] = None
                return await lingo_data(begin, end)
        except Exception as e:
            print('Exception from lingo_data()',e) # logger



async def get_token_QK():
    url = 'https://gate.97kid.com/t/user/login'
    payload = {
        "installationJsVersion": env['version'],
        "password": env['qk_password'],
        "username": env['qk_username']
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, ssl=False) as resp:
                token =  await resp.json()
                TEMP['token_QK'] = token['access_token']
    except Exception as e:
        logging.info("Couldn't get the QKid data. Start again")
        TEMP['token_QK'] = False
        return False


async def qkid_data(begin: int, week=False):
    if TEMP['token_QK'] is None:
        await get_token_QK()
    elif TEMP['token_QK'] == False:
        return False
    if week:
        extra = 604800 
    else:
        extra = 86400 # a day
    url = f'https://gate.97kid.com/t/calendars/my?beginAt={begin}&endAt={begin+extra}' 
    headers = {"authorization": f"Bearer {TEMP['token_QK']}"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, ssl=False, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data
                else:
                    print("We couldn't get the QK data, let's try again") # добавить в логгер
                    TEMP['token_QK'] = None
                return await qkid_data(begin, week)
    except Exception as e:
        print(f' УПС! нет данных от QKID {e}') # добавить в логгер
        return False

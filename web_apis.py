from dotenv import dotenv_values
import aiohttp


from util import async_timed

import logging
import pathlib
import os


DIR = pathlib.Path(__file__).parent.resolve()
env = dotenv_values(os.path.join(DIR, '.env'))

TEMP = {'token_lingo': None, 'token_QK': None}

logger = logging.getLogger(__name__)

async def get_token_lingo(session: aiohttp.ClientSession) -> None:
    url = 'https://teacher.lingoace.com/api/user/login'
    payload = {
        'identify': env['login'],
        'password': env['hash'],
        'plainPassword': env['password'],
        'role': env['role']
    }
    try:
        async with session.post(url, json=payload, ssl=False) as resp:
            token =  await resp.json()
            TEMP['token_lingo'] = token['data']['jwtToken']
    except Exception:
        logger.exception(f"Не пришел токен get_token_lingo()", exc_info=True)

@async_timed()
async def fetch_lingo_data(begin: str, end: str) -> dict:
    async with aiohttp.ClientSession() as session:
        while not TEMP['token_lingo']:
            await get_token_lingo(session)
        url = f"https://teacher.lingo-ace.com/api/schedule/tutor/self/timetable/publish/{env['tutor_id']}/{begin}/{end}/"
        headers = {"authorization": f"Bearer {TEMP['token_lingo']}"}
        try:
            async with session.get(url, ssl=False, headers=headers) as resp:
                data = await resp.json()
            if data['code'] != 200:
                logger.info(f"Не пришли данные от LingoAce. Ответ и код:<{data['message']} {data['code']}> Пробуем ещё.")
                TEMP['token_lingo'] = None
                return await fetch_lingo_data(begin, end)
            return data['data']
        except Exception as e:
            logger.exception(f'УПС! {fetch_lingo_data.__name__}:{e}', exc_info=True)



async def get_token_QK(session: aiohttp.ClientSession) -> None:
    url = 'https://gate.97kid.com/t/user/login'
    payload = {
        "installationJsVersion": env['version'],
        "password": env['qk_password'],
        "username": env['qk_username']
    }
    try:
        async with session.post(url, json=payload, ssl=False) as resp:
            token =  await resp.json()
            TEMP['token_QK'] = token['access_token']
    except Exception:
        logger.exception(f"Не пришел токен get_token_QK()", exc_info=True)

@async_timed()
async def fetch_qkid_data(begin: int, week: bool = False) -> list:
    async with aiohttp.ClientSession() as session:
        while TEMP['token_QK'] is None:
            await get_token_QK(session)
        if week: extra = 604800 
        else: extra = 86400 # a day
        url = f'https://gate.97kid.com/t/calendars/my?beginAt={begin}&endAt={begin+extra}' 
        headers = {"authorization": f"Bearer {TEMP['token_QK']}"}
        try:
            async with session.get(url, ssl=False, headers=headers) as resp:
                data = await resp.json()
                if resp.status == 200:
                    return data
                else:
                    logger.info(f"Не пришли данные от QKid. Ответ и код:<{data['message']} {data['code']} {resp.status}> Пробуем ещё.")
                    TEMP['token_QK'] = None
                return await fetch_qkid_data(begin, week)
        except Exception:
            logger.exception(f' УПС! нет данных от fetch_qkid_data()', exc_info=True)

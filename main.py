import aiohttp
import asyncio
import json
import logging
import sys
from datetime import datetime, timedelta
import platform


API_URL = 'https://api.privatbank.ua/p24api/exchange_rates?json&date='
CURRENCY_RATE = ['EUR', 'USD']

logging.basicConfig(format="%(message)s", level=logging.INFO)

class HttpError(Exception):
    pass


async def request(url: str):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result
                else:
                    raise HttpError(f"Error status: {resp.status} for {url}")
        except (aiohttp.ClientConnectorError, aiohttp.InvalidURL) as err:
            raise HttpError(f'Connection error: {url}', str(err))
        
        
        
def parser(argvs: list):
    if len(argvs) == 1:
        return 1
    
    if len(argvs) > 1 and 1 <= int(argvs[1]) <= 10:
        days = int(argvs[1])
    else:
        logging.info(f'Incorrect value, I can only give you the exchange rate for the last 10 days')
        days = None   
         
    if len(argvs) > 2:
        currencies = [c.upper() for c in argvs[2:]]
        for c in currencies:            
            if c.strip().upper() not in CURRENCY_RATE:                
                CURRENCY_RATE.append(c.strip().upper()) 
    return days


async def format_exchange_rates(result):
    data = {}
    for item in result['exchangeRate']:
        currency = item['currency']
        if currency in CURRENCY_RATE:
            data[currency] = {
                'sale': item['saleRateNB'],
                'purchase': item['purchaseRateNB']
            }
    return {result['date']: data}


async def main(interval):
    results = []
    today = datetime.now()
    for day in range(interval):    
        try:
            date = (today - timedelta(days=day)).strftime("%d.%m.%Y")
            response = await request(f'{API_URL}{date}')            
            results.append(await format_exchange_rates(response))
        except HttpError as err:
            print(err)
            return None    
    return results


if __name__ == '__main__':
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        interval= parser(sys.argv)
        if interval in range(10):
            formatted_results = asyncio.run(main(interval))
            logging.info(f"{json.dumps(formatted_results, indent=2)}")        
    except (ValueError, TypeError, IndexError) as err:
        logging.info(f'Errore: {err}')

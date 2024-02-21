import asyncio
import logging
import websockets
import names
from aiofile import async_open
from aiopath import AsyncPath
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK
from main import main

logging.basicConfig(level=logging.INFO)


async def exchange_log(data: list):
    file = AsyncPath("exchange_log.txt")

    if await file.exists():
        async with async_open("exchange_log", 'w') as fh:
            await fh.write(f"{await text_transform(data)}\n")
    else:
        async with async_open("exchange_log", 'a') as fh:
            await fh.write(f"{await text_transform(data)}\n")
            
            
async def text_transform(data: list) -> str:
    exchange = []
   
    for days in data:
        for date, values in days.items():
            day = f"Date: {date}"
            for currency, vs in values.items():
                if currency in ['EUR', 'USD']:
                    exchange.append(
                            f"{day} - {currency} sale: {vs['sale']}, purchase: {vs['purchase']}\n")

    return ''.join(exchange) if exchange else "No exchange"
       

async def get_exchange(days=1) -> str:
    
    result = await main(days)
    try:
        await exchange_log(result)
    except Exception as e:
        logging.error(e)

    return await text_transform(result)


class Server:
    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f'{ws.remote_address} connects')

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f'{ws.remote_address} disconnects')

    async def send_to_clients(self, message: str):
        if self.clients:
            [await client.send(message) for client in self.clients]

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distrubute(ws)
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    async def distrubute(self, ws: WebSocketServerProtocol):
        async for message in ws:
            if message.startswith("exchange"): 
                await self.send_to_clients("Please wait, your request is being processed...")
                cmd = message.split(' ')
                days = 1
                
                if len(cmd) > 1 and cmd[1].isdigit():
                    if int(cmd[1]) in range(10):
                        days = int(cmd[1]) 
                exchange = await get_exchange(days)
                await self.send_to_clients(exchange)
            elif message == 'Hello server':
                await self.send_to_clients("Hello! Can I halp you?")
            else:
                await self.send_to_clients(f"{ws.name}: {message}")


async def start():
    server = Server()
    async with websockets.serve(server.ws_handler, 'localhost', 8080):
        await asyncio.Future()  # run forever


if __name__ == '__main__':
    asyncio.run(start())


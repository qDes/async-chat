import os
import asyncio
import json
import logging

from dotenv import load_dotenv
from listen_minechat import get_current_time
from aioconsole import ainput


async def register(reader, writer):
    data = await reader.readline()
    await submit_message(writer)
    data = await reader.readline()
    print(json.loads(data))
    return None


async def authorise(reader, writer):
    #await submit_message(writer)
    message = await ainput(">>> ")
    message += "\n"
    writer.write(message.encode())
    await writer.drain()
    data = await reader.readline()
    data = json.loads(data)
    if data:
        logging.debug(f"Пользователь {data['nickname']} авторизован.")
        return True
    else:
        logging.debug('Токен невалидный. Проверьте его или зарегестрируйтесь заново.')
        return False

async def submit_message(writer):
    message = await ainput(">>> ")
    message += "\n\n"
    writer.write(message.encode())
    await writer.drain()


async def main(host, port):
    reader, writer = await asyncio.open_connection(host, port)
    data = await reader.read(2048)
    logging.debug(f"{data.decode()}")
    authorise_status = await authorise(reader, writer)
    if not authorise_status:
        await register(reader, writer)
    while True:
        await submit_message(writer)




if __name__ == "__main__":
    FORMAT = "%(levelname)s:sender: %(message)s"
    logging.basicConfig(format=FORMAT, level=logging.DEBUG)
    load_dotenv()
    token = os.environ.get("CHAT_TOKEN")
    asyncio.run(main('minechat.dvmn.org',5050))

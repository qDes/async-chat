import asyncio
import gui
import time
import configargparse
import logging
import json

from aiofile import AIOFile
from datetime import datetime


def get_current_time() -> str:
    now = datetime.now()
    return f"[{now.strftime('%x')} {now.strftime('%X')}] "


async def generate_msgs(queue):
    while True:
        timestamp = str(time.time()).split('.')[0]
        message = f"Ping {timestamp}"
        queue.put_nowait(message)
        await asyncio.sleep(1)


async def save_messages(history, queue):
    async with AIOFile(history, 'a+') as afp:
        while True:
            message = await queue.get()
            await afp.write(message)
            #print(message)


async def read_msgs(host, port, queue, history_queue):
    file_queue = asyncio.Queue()
    while True:
        try:
            connection_counter = 0
            reader, writer = await asyncio.open_connection(host, port)
            queue.put_nowait(f'{get_current_time()}Установлено соединение')
            while True:
                data = await reader.readline()
                message = get_current_time() + data.decode()
                queue.put_nowait(message)
                history_queue.put_nowait(message)
        except (ConnectionRefusedError,
                ConnectionResetError):
            queue.put_nowait('Нет соединения. Повторная попытка.')
            connection_counter += 1
            if connection_counter > 2:
                queue.put_nowait("Выход.")
                return None


async def authorise(reader, writer, token):
    message = token + "\n"
    writer.write(message.encode())
    await writer.drain()
    data = await reader.readline()
    data = json.loads(data)
    if data:
        logging.debug(f"Пользователь {data['nickname']} авторизован.")
        return True
    else:
        logging.debug("Токен невалидный. Проверьте его или зарегестрируйтесь заново.")
        return False


async def send_msgs(host, port, queue, token):
    reader, writer = await asyncio.open_connection(host, port)
    data = await reader.readline()
    logging.debug(f"{data.decode()}")
    if token:
        auth_status = await authorise(reader, writer, token)
    while True:
        msg = await queue.get()
        print(msg) 


def load_history(history, queue):
    with open("minechat.history", 'r') as f:
        for line in f.readlines():
            queue.put_nowait(line)


async def main():
    parser = configargparse.ArgParser(default_config_files=['.env'])
    parser.add('--host', required=True,
               help='chat host address')
    parser.add('--port_listen', required=True, type=int,
               help='chat listen port')
    parser.add('--history', required=True,
               help='history writing file')
    parser.add('--port_write', required=True, type=int,
               help='chat write port')
    parser.add('--token', help='user connection token')   
    args = parser.parse_args()
    host, port_listen, history = args.host, args.port_listen, args.history
    port_write, token = args.port_write, args.token
    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()
    history_queue = asyncio.Queue()
    load_history(history, messages_queue)
    await asyncio.gather(
            save_messages(history, history_queue),
            send_msgs(host, port_write, sending_queue, token),
            read_msgs(host, port_listen, messages_queue, history_queue),
            gui.draw(messages_queue, sending_queue, status_updates_queue)
            )


if __name__ == "__main__":
    asyncio.run(main())

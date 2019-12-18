import asyncio
import gui
import time
import configargparse

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


async def main():
    parser = configargparse.ArgParser(default_config_files=['.env_listen'])
    parser.add('--host', required=True,
               help='chat host address')
    parser.add('--port', required=True, type=int,
               help='chat listen port')
    parser.add('--history', required=True,
               help='history writing file')
    args = parser.parse_args()
    host, port, history = args.host, args.port, args.history
    print(history)
    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()
    history_queue = asyncio.Queue()
    await asyncio.gather(
            save_messages(history, history_queue),
            read_msgs(host, port, messages_queue, history_queue),
            gui.draw(messages_queue, sending_queue, status_updates_queue)
            )


if __name__ == "__main__":
    asyncio.run(main())

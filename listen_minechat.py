import asyncio
import configargparse

from datetime import datetime
from aiofile import AIOFile


def get_current_time() -> str:
    now = datetime.now()
    return f"[{now.strftime('%x')} {now.strftime('%X')}] "


async def client(HOST, PORT, HIST_FILE):
    while True:
        connection_counter = 0
        try:
            reader, writer = await asyncio.open_connection(HOST, PORT)
        except (ConnectionRefusedError,
                ConnectionResetError):
            print('Нет соединения. Повторная попытка.')
            connection_counter += 1
            if connection_counter > 2:
                print("Выход.")
                return None
        print(f'{get_current_time()}Установлено соединение')
        async with AIOFile(HIST_FILE, 'a+') as afp:
            while True:
                data = await reader.readline()
                message = get_current_time() + data.decode()
                print(message)
                await afp.write(message)


if __name__ == "__main__":
    parser = configargparse.ArgParser(default_config_files=['.env_listen'])
    parser.add('--host', required=True,
               help='chat host address')
    parser.add('--port', required=True, type=int,
               help='chat listen port')
    parser.add('--history', required=True,
               help='history writing file')
    args = parser.parse_args()
    HOST, PORT, HIST_FILE = args.host, args.port, args.history
    asyncio.run(client(HOST, PORT, HIST_FILE))

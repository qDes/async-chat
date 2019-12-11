import asyncio
import configargparse

from datetime import datetime
from aiofile import AIOFile


def get_current_time() -> str:
    now = datetime.now()
    return f"[{now.strftime('%x')} {now.strftime('%X')}] "


async def client(host, port, history):
    while True:
        try:
            connection_counter = 0
            reader, writer = await asyncio.open_connection(host, port)
            print(f'{get_current_time()}Установлено соединение')
            async with AIOFile(history, 'a+') as afp:
                while True:
                    data = await reader.readline()
                    message = get_current_time() + data.decode()
                    print(message)
                    await afp.write(message)
        except (ConnectionRefusedError,
                ConnectionResetError):
            print('Нет соединения. Повторная попытка.')
            connection_counter += 1
            if connection_counter > 2:
                print("Выход.")
                return None


def main():
    parser = configargparse.ArgParser(default_config_files=['.env_listen'])
    parser.add('--host', required=True,
               help='chat host address')
    parser.add('--port', required=True, type=int,
               help='chat listen port')
    parser.add('--history', required=True,
               help='history writing file')
    args = parser.parse_args()
    host, port, history = args.host, args.port, args.history
    asyncio.run(client(host, port, history))


if __name__ == "__main__":
    main()

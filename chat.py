import asyncio
import gui
import time
import configargparse
import logging
import json

from aiofile import AIOFile
from datetime import datetime
from tkinter import messagebox


class InvalidToken(Exception):
    pass


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


async def read_msgs(host, port, read_queue, history_queue, status_queue):
    file_queue = asyncio.Queue()
    while True:
        try:
            connection_counter = 0
            status_queue.put_nowait(gui.ReadConnectionStateChanged.INITIATED)
            reader, writer = await asyncio.open_connection(host, port)
            read_queue.put_nowait(f'{get_current_time()}Установлено соединение.\n')
            status_queue.put_nowait(gui.ReadConnectionStateChanged.ESTABLISHED)
            while True:
                data = await reader.readline()
                message = get_current_time() + data.decode()
                read_queue.put_nowait(message)
                history_queue.put_nowait(message)
        except (ConnectionRefusedError,
                ConnectionResetError):
            queue.put_nowait('Нет соединения. Повторная попытка.')
            connection_counter += 1
            if connection_counter > 2:
                read_queue.put_nowait("Выход.")
                return None


async def authorise(reader, writer, token):
    if not token:
        logging.debug("Пустой токен")
        raise InvalidToken
    message = token + "\n"
    writer.write(message.encode())
    await writer.drain()
    data = await reader.readline()
    data = json.loads(data)
    print(data)
    nickname = data.get("nickname")
    #if data:
        #logging.debug(f"Пользователь {data['nickname']} авторизован.")
        #return True
    if not data:
        logging.debub("Токен невалидный")
        raise InvalidToken
    return nickname
    #else:
        #logging.debug("Токен невалидный. Проверьте его или зарегестрируйтесь заново.")
        #return False


async def submit_message(writer, message):
    message += "\n\n"
    logging.debug(f"send message - {message}")
    writer.write(message.encode())
    await writer.drain()


async def send_msgs(host, port, msgs_queue, status_queue, token):
    status_queue.put_nowait(gui.SendingConnectionStateChanged.INITIATED)
    reader, writer = await asyncio.open_connection(host, port)
    data = await reader.readline()
    logging.debug(f"{data.decode()}")
    nickname = await authorise(reader, writer, token)
    event = gui.NicknameReceived(nickname)
    status_queue.put_nowait(event)
    status_queue.put_nowait(gui.SendingConnectionStateChanged.ESTABLISHED)
    while True:
        msg = await msgs_queue.get()
        await submit_message(writer, msg)  


def load_history(history, queue):
    with open("minechat.history", 'r') as f:
        for line in f.readlines():
            queue.put_nowait(line)


async def main():
    FORMAT = "%(levelname)s:sender: %(message)s"
    logging.basicConfig(format=FORMAT, level=logging.DEBUG)
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
    print(token)
    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()
    history_queue = asyncio.Queue()
    load_history(history, messages_queue)
    await asyncio.gather(
            save_messages(history, history_queue),
            send_msgs(host, port_write, sending_queue,
                      status_updates_queue, token),
            read_msgs(host, port_listen, messages_queue, 
                      history_queue, status_updates_queue),
            gui.draw(messages_queue, sending_queue, status_updates_queue)
            )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, gui.TkAppClosed):
        print("Exit")
    except InvalidToken:
        messagebox.showinfo("Неверный токен", "Проверьте токен")

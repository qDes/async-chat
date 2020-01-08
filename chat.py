import asyncio
import contextlib
import gui
import time
import configargparse
import logging
import json
import socket

from aiofile import AIOFile
from aionursery import Nursery, MultiError
from async_timeout import timeout
from asyncio import TimeoutError
from datetime import datetime
from gui import TkAppClosed
from functools import wraps
from reg import RegistrationGUI
from tkinter import messagebox, Tk


@contextlib.asynccontextmanager
async def create_handy_nursery():
    try:
        async with Nursery() as nursery:
            yield nursery
    except MultiError as e:
        if len(e.exceptions) == 1:
            # suppress exception chaining
            # https://docs.python.org/3/reference/simple_stmts.html#the-raise-statement
            raise e.exceptions[0] from None
        raise


def reconnect(func):
    @wraps(func)
    async def wrapped(*args, **kwargs):
        while True:
            try:
                return await func(*args, **kwargs)
            except (ConnectionError,
                    socket.gaierror,
                    MultiError):
                await asyncio.sleep(1)
    return wrapped


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


async def read_msgs(host, port, read_queue, 
                    history_queue, status_queue, watchdog_queue):
    file_queue = asyncio.Queue()
    status_queue.put_nowait(gui.ReadConnectionStateChanged.INITIATED)
    reader, writer = await asyncio.open_connection(host, port)
    read_queue.put_nowait(f'{get_current_time()}Установлено соединение.\n')
    status_queue.put_nowait(gui.ReadConnectionStateChanged.ESTABLISHED)
    while True:
        data = await reader.readline()
        message = get_current_time() + data.decode()
        watchdog_queue.put_nowait("New message in chat")
        read_queue.put_nowait(message)
        history_queue.put_nowait(message)


async def authorise(reader, writer, token):
    if not token:
        logging.debug("Пустой токен")
        raise InvalidToken
    message = token + "\n"
    writer.write(message.encode())
    await writer.drain()
    data = await reader.readline()
    data = json.loads(data)
    nickname = data.get("nickname")
    if not data:
        logging.debub("Токен невалидный")
        raise InvalidToken
    return nickname


async def submit_message(writer, message):
    message += "\n\n"
    logging.debug(f"send message - {message}")
    writer.write(message.encode())
    await writer.drain()


async def send_msgs(host, port, msgs_queue, 
                    status_queue, watchdog_queue, token):
    status_queue.put_nowait(gui.SendingConnectionStateChanged.INITIATED)
    reader, writer = await asyncio.open_connection(host, port)
    data = await reader.readline()
    logging.debug(f"{data.decode()}")
    watchdog_queue.put_nowait('Promt before auth')
    nickname = await authorise(reader, writer, token)
    watchdog_queue.put_nowait("Auth done")
    event = gui.NicknameReceived(nickname)
    status_queue.put_nowait(event)
    status_queue.put_nowait(gui.SendingConnectionStateChanged.ESTABLISHED)
    async with create_handy_nursery() as nursery:
        nursery.start_soon(ping_server(writer, reader, watchdog_queue))
        nursery.start_soon(send_to_chat(writer, msgs_queue, watchdog_queue))
    

async def ping_server(writer, reader, watchdog_queue):
    while True:
        writer.write(b"\n")
        await writer.drain()
        msg = await reader.readline()
        if msg:
            watchdog_queue.put_nowait('Reply from server.')
        await asyncio.sleep(2)

        

async def send_to_chat(writer, msgs_queue, watchdog_queue):
    while True:
        msg = await msgs_queue.get()
        watchdog_queue.get()
        await submit_message(writer, msg)


def load_history(history, queue):
    with open("minechat.history", 'r') as f:
        for line in f.readlines():
            queue.put_nowait(line)


async def watch_for_connection(watchdog_queue):
    watchdog_logger = logging.getLogger('watchdog')
    watchdog_logger.setLevel(logging.DEBUG)
    TIMEOUT = 5
    while True:
        try:
            async with timeout(TIMEOUT) as cm:
                msg = await watchdog_queue.get()
                msg = f"[{int(time.time())}] Connection is alive. {msg}"
                watchdog_logger.info(msg)
        except TimeoutError:
            raise ConnectionError


def parse_args():
    parser = configargparse.ArgParser(default_config_files=['.env','.token'])
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
    return (args.host, args.port_listen, args.history,
            args.port_write, args.token)


@reconnect
async def handle_connection(host, port_listen, history, 
                            port_write, token,
                            messages_queue,
                            sending_queue,
                            status_updates_queue,
                            history_queue): 
    watchdog_queue = asyncio.Queue()
    async with create_handy_nursery() as nursery:
        nursery.start_soon(read_msgs(host, port_listen, messages_queue,
                                     history_queue, status_updates_queue,
                                     watchdog_queue))
        nursery.start_soon(save_messages(history, history_queue))
        nursery.start_soon(send_msgs(host, port_write,
                                     sending_queue, status_updates_queue,
                                     watchdog_queue, token))
        nursery.start_soon(watch_for_connection(watchdog_queue))


async def main():
    FORMAT = "%(levelname)s:sender: %(message)s"
    logging.basicConfig(format=FORMAT, level=logging.DEBUG)
    host, port_listen, history, port_write, token = parse_args()
    print(token)
    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()
    history_queue = asyncio.Queue()
    load_history(history, messages_queue) 
    async with create_handy_nursery() as nursery:
        nursery.start_soon(handle_connection(host, port_listen, 
                           history, port_write, token,
                           messages_queue,
                           sending_queue,
                           status_updates_queue,
                           history_queue))
        nursery.start_soon(gui.draw(messages_queue, 
                                    sending_queue, 
                                    status_updates_queue))
 


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, TkAppClosed):
        print("Exit")
    except InvalidToken:
        # messagebox.showinfo("Неверный токен", "Проверьте токен")
        root = Tk()
        reg_gui = RegistrationGUI(root)
        root.mainloop()

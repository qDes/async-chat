import asyncio
import json
import logging

import configargparse
from aioconsole import ainput


async def register(reader, writer, username):
    message = '\n'
    writer.write(message.encode())
    await writer.drain()
    data = await reader.readline()
    username += '\n'
    writer.write(username.encode())
    await writer.drain()
    data = await reader.readline()
    profile = json.loads(data)
    print(f"Your nick: {profile['nickname']}, your token: {profile['account_hash']}")
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


async def submit_message(writer, message=None):
    if not message:
        message = await ainput(">>> ")
    message += "\n\n"
    logging.debug(f"send message - {message}")
    writer.write(message.encode())
    await writer.drain()


async def main(host, port, token, message, username):
    auth_status = False
    reader, writer = await asyncio.open_connection(host, port)
    data = await reader.readline()
    logging.debug(f"{data.decode()}")
    if token:
        auth_status = await authorise(reader, writer, token)
    if not auth_status and not username:
        logging.debug(f"Enter username for new user register or valid token.")
        return None
    if username and not auth_status:
        await register(reader, writer, username)
    if message:
        await submit_message(writer, message)
    else:
        while True:
            await submit_message(writer)


if __name__ == "__main__":
    FORMAT = "%(levelname)s:sender: %(message)s"
    logging.basicConfig(format=FORMAT, level=logging.DEBUG)
    parser = configargparse.ArgParser(description='minechat message sender',
                                      default_config_files=['.env_write'])
    parser.add("--host", required=True,
               help="chat host address")
    parser.add('--port', required=True, type=int,
               help='chat write port')
    parser.add('--token', help='user connection token')
    parser.add('--message', help='message to chat')
    parser.add('--username', help='username of unregistered user')
    args = parser.parse_args()
    host, port, token = args.host, args.port, args.token
    message, username = args.message, args.username
    asyncio.run(main(host, port, token, message, username))

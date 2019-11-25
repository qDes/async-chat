import os
import asyncio

from dotenv import load_dotenv
from listen_minechat import get_current_time
from aioconsole import ainput


async def write_to_chat(HOST, PORT, TOKEN):
    reader, writer = await asyncio.open_connection(HOST,PORT)
    data = await reader.read(2048)
    TOKEN += '\n'
    print(data)
    writer.write(TOKEN.encode())
    await writer.drain()
    data = await reader.read(2048)
    print(data)
    writer.write('test \n\n'.encode()) 
    await writer.drain()
    
    while True:
        message = await ainput(">>>")
        message += '\n\n'
        writer.write(message.encode())
        await writer.drain()

'''
async def main(host, port, token):
'''


if __name__ == "__main__":
    load_dotenv()
    token = os.environ.get("CHAT_TOKEN")
    #print(token)
    asyncio.run(write_to_chat('minechat.dvmn.org',5050,token))

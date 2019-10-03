import asyncio 
import argparse
from datetime import datetime
from aiofile import AIOFile, Reader, Writer

def get_current_time() -> str:
    now = datetime.now()
    return f"[{now.strftime('%x')} {now.strftime('%X')}] " 

async def client(HOST, PORT, HIST_FILE):
    while True:
        
        try:
            reader, writer = await asyncio.open_connection(
                    HOST, PORT)
        except (ConnectionRefusedError, 
                ConnectionResetError) as err:
            print('Нет соединения.')
        print(f'{get_current_time()} Установлено соединение')
        
        async with AIOFile(HIST_FILE, 'a+') as afp:    
            while True:
                data = await reader.read(2048)
                #get rid of empty messages
                if len(data) > 2:
                    message = get_current_time() + data.decode()
                    await afp.write(message)
                print(message)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Async connection to minechat')
    parser.add_argument('--host',action='store',help = 'set chat addr',
            default = 'minechat.dvmn.org')
    parser.add_argument('--port',action='store',type=int,help='set char port',
            default=5000)
    parser.add_argument('--history',action='store',help='set history file',
            default='minechat.history')
    args = parser.parse_args()
    HOST, PORT, HIST_FILE = args.host, args.port, args.history

    asyncio.run(client(HOST, PORT, HIST_FILE))

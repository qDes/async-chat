import asyncio
import gui
import time


async def generate_msgs(queue):
    while True:
        timestamp = str(time.time()).split('.')[0]
        message = f"Ping {timestamp}"
        queue.put_nowait(message)
        await asyncio.sleep(1)


async def main():
    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()
    await asyncio.gather(
            generate_msgs(messages_queue),
            gui.draw(messages_queue, sending_queue, status_updates_queue)
            )

if __name__ == "__main__":
    asyncio.run(main())

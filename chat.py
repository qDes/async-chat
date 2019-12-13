import asyncio
import gui

loop = asyncio.get_event_loop()

messages_queue = asyncio.Queue()
sending_queue = asyncio.Queue()
status_updates_queue = asyncio.Queue()

messages_queue.put_nowait('Привет всем в этом чатике!')
messages_queue.put_nowait('Как дела?')


loop.run_until_complete(gui.draw(messages_queue, sending_queue, status_updates_queue))

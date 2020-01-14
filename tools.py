import contextlib

from aionursery import Nursery, MultiError
from functools import wraps


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

import functools
import time


def async_timed():
    def wrapper(func):
        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            start = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                print(f"{func} завершилась за {time.time() - start} сек")
        return wrapped

    return wrapper
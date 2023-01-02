import functools
import time
import logging


logger = logging.getLogger(__name__)

def async_timed():
    def wrapper(func):
        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            start = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                logger.info(f"{func.__name__} завершилась за {time.time() - start} сек")
        return wrapped

    return wrapper
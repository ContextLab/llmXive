import signal
import time
from contextlib import contextmanager
from functools import wraps
from typing import Callable, Optional

class TimeoutError(Exception):
    pass

@contextmanager
def timeout_context(seconds: int):
    def handler(signum, frame):
        raise TimeoutError("Function call timed out")
    
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)

def timeout_decorator(seconds: int):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with timeout_context(seconds):
                return func(*args, **kwargs)
        return wrapper
    return decorator

def enforce_timeout(func: Callable, timeout_seconds: int):
    def handler(signum, frame):
        raise TimeoutError("Function call timed out")
    
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(timeout_seconds)
    try:
        result = func()
        return result
    finally:
        signal.alarm(0)

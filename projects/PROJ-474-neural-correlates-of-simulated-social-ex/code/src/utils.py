import logging
import sys
import os
import traceback
from typing import Optional, Dict, Any
from pathlib import Path

def setup_logging(log_file: Optional[Path] = None, level: int = logging.INFO) -> None:
    """
    Initialise a basic logger. If ``log_file`` is supplied the logs are also
    written to that file, otherwise they are only emitted to ``stderr``.
    """
    handlers = [logging.StreamHandler(sys.stderr)]
    if log_file is not None:
        handlers.append(logging.FileHandler(log_file))
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )

def get_logger(name: str = __name__) -> logging.Logger:
    """
    Return a logger instance for the given ``name``.
    """
    return logging.getLogger(name)

def log_exception(*args, **kwargs) -> None:
    """
    Log an exception in a very tolerant way.

    The function is deliberately permissive because it is called from many
    different places in the code base with slightly different signatures.
    It accepts:

    * ``log_exception(logger)`` – only a logger is supplied.
    * ``log_exception(logger, exc)`` – a logger and an exception.
    * ``log_exception(logger=..., exc=...)`` – keyword arguments.
    * ``log_exception(exc=exc)`` – only an exception (logger defaults to root).
    * ``log_exception()`` – nothing; a generic “exception occurred” message is logged.

    Any combination of positional and keyword arguments is handled.
    """
    # Resolve logger
    logger = None
    if "logger" in kwargs:
        logger = kwargs["logger"]
    elif args:
        logger = args[0]

    if logger is None:
        logger = logging.getLogger()

    # Resolve exception
    exc = kwargs.get("exc")
    if exc is None and len(args) > 1:
        exc = args[1]

    # If an exception object is supplied, log its traceback; otherwise log a generic message.
    if exc is not None:
        if isinstance(exc, BaseException):
            logger.error("Exception occurred:", exc_info=exc)
        else:
            # ``exc`` might be a string or other object – treat it as a message.
            logger.error(f"Exception occurred: {exc}")
    else:
        # No explicit exception – log the current traceback (if any)
        logger.exception("An exception occurred")
"""Simple logger wrapper used throughout the project.

The module provides :func:`get_logger` which returns a ``logging.Logger``
instance configured with a standard format.  The function is public and
documented.
"""

import logging

def get_logger(name: str):
    """Return a logger with a predefined format.

    Parameters
    ----------
    name : str
        Name of the logger (typically ``__name__``).

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

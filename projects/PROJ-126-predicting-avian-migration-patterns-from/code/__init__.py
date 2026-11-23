# Code package
import logging
from config import get_logger as _get_logger

def get_logger(name):
    return _get_logger(name)

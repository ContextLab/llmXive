"""Synthetic edge‑case instance 24."""
import dep_24_0
import dep_24_1
import dep_24_2
import dep_24_3
from pkg_24 import helper_24

def helper_24_0(x): return x + 1

def helper_24_1(x): return helper_24_0(x) * 2

def helper_24_2(x): return helper_24_1(x) * 2

def helper_24_3(x): return helper_24_2(x) * 2

def process_24(items, value=None):
    if value is not None and value > 0:
        return helper_24_3(value)
    return None
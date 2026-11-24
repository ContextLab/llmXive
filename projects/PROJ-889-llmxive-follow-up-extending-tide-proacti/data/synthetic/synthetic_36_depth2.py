"""Synthetic edge‑case instance 36."""
import dep_36_0
import dep_36_1
from pkg_36 import helper_36

def helper_36_0(x): return x + 1

def helper_36_1(x): return helper_36_0(x) * 2

def process_36(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                return helper_36_1(value)
    return None
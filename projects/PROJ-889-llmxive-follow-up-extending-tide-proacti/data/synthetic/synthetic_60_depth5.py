"""Synthetic edge‑case instance 60."""
import dep_60_0
import dep_60_1
import dep_60_2
import dep_60_3
import dep_60_4
from pkg_60 import helper_60

def helper_60_0(x): return x + 1

def helper_60_1(x): return helper_60_0(x) * 2

def helper_60_2(x): return helper_60_1(x) * 2

def helper_60_3(x): return helper_60_2(x) * 2

def helper_60_4(x): return helper_60_3(x) * 2

def process_60(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                return helper_60_4(value)
    return None
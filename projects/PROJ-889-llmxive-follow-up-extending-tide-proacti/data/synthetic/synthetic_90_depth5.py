"""Synthetic edge‑case instance 90."""
import dep_90_0
import dep_90_1
import dep_90_2
import dep_90_3
import dep_90_4
from pkg_90 import helper_90

def helper_90_0(x): return x + 1

def helper_90_1(x): return helper_90_0(x) * 2

def helper_90_2(x): return helper_90_1(x) * 2

def helper_90_3(x): return helper_90_2(x) * 2

def helper_90_4(x): return helper_90_3(x) * 2

def process_90(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                if value is not None and value > 3:
                    return helper_90_4(value)
    return None
"""Synthetic edge‑case instance 198."""
import dep_198_0
import dep_198_1
import dep_198_2
from pkg_198 import helper_198

def helper_198_0(x): return x + 1

def helper_198_1(x): return helper_198_0(x) * 2

def helper_198_2(x): return helper_198_1(x) * 2

def process_198(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            return helper_198_2(value)
    return None
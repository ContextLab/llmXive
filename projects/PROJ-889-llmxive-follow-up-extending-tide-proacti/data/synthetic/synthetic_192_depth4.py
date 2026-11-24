"""Synthetic edge‑case instance 192."""
import dep_192_0
import dep_192_1
import dep_192_2
import dep_192_3
from pkg_192 import helper_192

def helper_192_0(x): return x + 1

def helper_192_1(x): return helper_192_0(x) * 2

def helper_192_2(x): return helper_192_1(x) * 2

def helper_192_3(x): return helper_192_2(x) * 2

def process_192(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                return helper_192_3(value)
    return None
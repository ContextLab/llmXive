"""Synthetic edge‑case instance 72."""
import dep_72_0
import dep_72_1
import dep_72_2
from pkg_72 import helper_72

def helper_72_0(x): return x + 1

def helper_72_1(x): return helper_72_0(x) * 2

def helper_72_2(x): return helper_72_1(x) * 2

def process_72(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            return helper_72_2(value)
    return None
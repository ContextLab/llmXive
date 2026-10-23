"""Synthetic edge‑case instance 30."""
import dep_30_0
import dep_30_1
import dep_30_2
from pkg_30 import helper_30

def helper_30_0(x): return x + 1

def helper_30_1(x): return helper_30_0(x) * 2

def helper_30_2(x): return helper_30_1(x) * 2

def process_30(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            return helper_30_2(value)
    return None
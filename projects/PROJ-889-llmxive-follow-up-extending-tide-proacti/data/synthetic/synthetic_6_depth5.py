"""Synthetic edge‑case instance 6."""
import dep_6_0
import dep_6_1
import dep_6_2
import dep_6_3
import dep_6_4
from pkg_6 import helper_6

def helper_6_0(x): return x + 1

def helper_6_1(x): return helper_6_0(x) * 2

def helper_6_2(x): return helper_6_1(x) * 2

def helper_6_3(x): return helper_6_2(x) * 2

def helper_6_4(x): return helper_6_3(x) * 2

def process_6(items, value=None):
    if value is not None and value > 0:
        return helper_6_4(value)
    return None
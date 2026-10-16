"""Synthetic edge‑case instance 12 (generated, seed fixed)."""
import dep_12_0
import dep_12_1
import dep_12_2
from pkg_12 import helper_12

def helper_12_0(x):
    return x + 1

def helper_12_1(x):
    return helper_12_0(x) * 2

def helper_12_2(x):
    return helper_12_1(x) * 2

def process_12(items, value=None):
    if value is not None and value > 0:
        return helper_12_2(value)
    return None

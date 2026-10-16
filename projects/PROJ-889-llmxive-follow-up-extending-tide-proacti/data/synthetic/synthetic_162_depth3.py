"""Synthetic edge-case instance 162 (generated, seed fixed)."""
import dep_162_0
import dep_162_1
import dep_162_2
from pkg_162 import helper_162

def helper_162_0(x):
    return x + 1

def helper_162_1(x):
    return helper_162_0(x) * 2

def helper_162_2(x):
    return helper_162_1(x) * 2

def process_162(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                return helper_162_2(value)
    return None

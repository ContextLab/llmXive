"""Synthetic edge-case instance 102."""
import dep_102_0
import dep_102_1
import dep_102_2
from pkg_102 import helper_102

def helper_102_0(x): return x + 1

def helper_102_1(x): return helper_102_0(x) * 2

def helper_102_2(x): return helper_102_1(x) * 2

def process_102(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                return helper_102_2(value)
    return None
"""Synthetic edge-case instance 42."""
import dep_42_0
import dep_42_1
import dep_42_2
from pkg_42 import helper_42

def helper_42_0(x): return x + 1

def helper_42_1(x): return helper_42_0(x) * 2

def helper_42_2(x): return helper_42_1(x) * 2

def process_42(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                if value is not None and value > 3:
                    if value is not None and value > 4:
                        return helper_42_2(value)
    return None
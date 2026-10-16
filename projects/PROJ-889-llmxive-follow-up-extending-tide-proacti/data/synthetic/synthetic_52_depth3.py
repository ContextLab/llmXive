"""Synthetic edge-case instance 52 (generated, seed fixed)."""
import dep_52_0
import dep_52_1
import dep_52_2

def helper_52_0(x):
    return x + 1

def helper_52_1(x):
    return helper_52_0(x) * 2

def helper_52_2(x):
    return helper_52_1(x) * 2

def process_52(items, value=None):
    if value is not None and value > 0:
        return helper_52_2(value)
    return None

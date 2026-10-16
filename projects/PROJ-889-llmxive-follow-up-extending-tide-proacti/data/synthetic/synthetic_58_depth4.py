"""Synthetic edge‑case instance 58 (generated, seed fixed)."""
import dep_58_0
import dep_58_1
import dep_58_2
import dep_58_3

def helper_58_0(x):
    return x + 1

def helper_58_1(x):
    return helper_58_0(x) * 2

def helper_58_2(x):
    return helper_58_1(x) * 2

def helper_58_3(x):
    return helper_58_2(x) * 2

def process_58(items, value=None):
    if value is not None and value > 0:
        return helper_58_3(value)
    return None

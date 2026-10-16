"""Synthetic edge‑case instance 62 (generated, seed fixed)."""
import dep_62_0
import dep_62_1
import dep_62_2

def helper_62_0(x):
    return x + 1

def helper_62_1(x):
    return helper_62_0(x) * 2

def helper_62_2(x):
    return helper_62_1(x) * 2

def process_62(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                return helper_62_2(value)
    return None

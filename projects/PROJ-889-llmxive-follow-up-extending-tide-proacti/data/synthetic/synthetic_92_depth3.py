"""Synthetic edge‑case instance 92 (generated, seed fixed)."""
import dep_92_0
import dep_92_1
import dep_92_2

def helper_92_0(x):
    return x + 1

def helper_92_1(x):
    return helper_92_0(x) * 2

def helper_92_2(x):
    return helper_92_1(x) * 2

def process_92(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            return helper_92_2(value)
    return None

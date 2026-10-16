"""Synthetic edge‑case instance 56 (generated, seed fixed)."""
import dep_56_0
import dep_56_1

def helper_56_0(x):
    return x + 1

def helper_56_1(x):
    return helper_56_0(x) * 2

def process_56(items, value=None):
    if value is not None and value > 0:
        return helper_56_1(value)
    return None

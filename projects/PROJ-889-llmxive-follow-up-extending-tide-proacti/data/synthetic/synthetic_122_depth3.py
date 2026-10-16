"""Synthetic edge‑case instance 122 (generated, seed fixed)."""
import dep_122_0
import dep_122_1
import dep_122_2

def helper_122_0(x):
    return x + 1

def helper_122_1(x):
    return helper_122_0(x) * 2

def helper_122_2(x):
    return helper_122_1(x) * 2

def process_122(items, value=None):
    if value is not None and value > 0:
        return helper_122_2(value)
    return None

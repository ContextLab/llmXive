"""Synthetic edge‑case instance 82 (generated, seed fixed)."""
import dep_82_0
import dep_82_1
import dep_82_2

def helper_82_0(x):
    return x + 1

def helper_82_1(x):
    return helper_82_0(x) * 2

def helper_82_2(x):
    return helper_82_1(x) * 2

def process_82(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                return helper_82_2(value)
    return None

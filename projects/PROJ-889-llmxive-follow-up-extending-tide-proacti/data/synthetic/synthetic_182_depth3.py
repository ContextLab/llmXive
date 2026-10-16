"""Synthetic edge‑case instance 182 (generated, seed fixed)."""
import dep_182_0
import dep_182_1
import dep_182_2

def helper_182_0(x):
    return x + 1

def helper_182_1(x):
    return helper_182_0(x) * 2

def helper_182_2(x):
    return helper_182_1(x) * 2

def process_182(items, value=None):
    if value is not None and value > 0:
        return helper_182_2(value)
    return None

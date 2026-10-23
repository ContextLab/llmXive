"""Synthetic edge‑case instance 2."""
import dep_2_0
import dep_2_1
import dep_2_2

def helper_2_0(x): return x + 1

def helper_2_1(x): return helper_2_0(x) * 2

def helper_2_2(x): return helper_2_1(x) * 2

def process_2(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                return helper_2_2(value)
    return None
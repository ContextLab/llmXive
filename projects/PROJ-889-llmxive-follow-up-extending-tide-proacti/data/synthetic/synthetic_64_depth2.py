"""Synthetic edge‑case instance 64."""
import dep_64_0
import dep_64_1

def helper_64_0(x): return x + 1

def helper_64_1(x): return helper_64_0(x) * 2

def process_64(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                return helper_64_1(value)
    return None
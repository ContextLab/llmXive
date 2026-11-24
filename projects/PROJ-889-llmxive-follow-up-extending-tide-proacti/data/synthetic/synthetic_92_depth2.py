"""Synthetic edge‑case instance 92."""
import dep_92_0
import dep_92_1

def helper_92_0(x): return x + 1

def helper_92_1(x): return helper_92_0(x) * 2

def process_92(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            return helper_92_1(value)
    return None
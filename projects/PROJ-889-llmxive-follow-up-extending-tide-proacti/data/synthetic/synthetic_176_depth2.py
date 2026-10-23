"""Synthetic edge‑case instance 176."""
import dep_176_0
import dep_176_1

def helper_176_0(x): return x + 1

def helper_176_1(x): return helper_176_0(x) * 2

def process_176(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                return helper_176_1(value)
    return None
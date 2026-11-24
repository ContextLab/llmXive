"""Synthetic edge‑case instance 148."""
import dep_148_0
import dep_148_1

def helper_148_0(x): return x + 1

def helper_148_1(x): return helper_148_0(x) * 2

def process_148(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                return helper_148_1(value)
    return None
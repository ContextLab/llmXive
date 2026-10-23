"""Synthetic edge‑case instance 106."""
import dep_106_0
import dep_106_1

def helper_106_0(x): return x + 1

def helper_106_1(x): return helper_106_0(x) * 2

def process_106(items, value=None):
    if value is not None and value > 0:
        return helper_106_1(value)
    return None
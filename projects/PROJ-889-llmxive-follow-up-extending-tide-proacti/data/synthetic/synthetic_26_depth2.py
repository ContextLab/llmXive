"""Synthetic edge-case instance 26."""
import dep_26_0
import dep_26_1

def helper_26_0(x): return x + 1

def helper_26_1(x): return helper_26_0(x) * 2

def process_26(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                if value is not None and value > 3:
                    return helper_26_1(value)
    return None
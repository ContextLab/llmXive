"""Synthetic edge-case instance 136."""
import dep_136_0
import dep_136_1

def helper_136_0(x): return x + 1

def helper_136_1(x): return helper_136_0(x) * 2

def process_136(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                return helper_136_1(value)
    return None
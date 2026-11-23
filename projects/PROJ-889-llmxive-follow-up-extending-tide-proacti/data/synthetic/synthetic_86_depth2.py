"""Synthetic edge-case instance 86."""
import dep_86_0
import dep_86_1

def helper_86_0(x): return x + 1

def helper_86_1(x): return helper_86_0(x) * 2

def process_86(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            return helper_86_1(value)
    return None
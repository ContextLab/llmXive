"""Synthetic edge‑case instance 184."""
import dep_184_0
import dep_184_1
import dep_184_2

def helper_184_0(x): return x + 1

def helper_184_1(x): return helper_184_0(x) * 2

def helper_184_2(x): return helper_184_1(x) * 2

def process_184(items, value=None):
    if value is not None and value > 0:
        return helper_184_2(value)
    return None
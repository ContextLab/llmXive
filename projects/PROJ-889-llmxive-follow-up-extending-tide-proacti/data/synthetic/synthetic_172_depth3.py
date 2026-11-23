"""Synthetic edge-case instance 172."""
import dep_172_0
import dep_172_1
import dep_172_2

def helper_172_0(x): return x + 1

def helper_172_1(x): return helper_172_0(x) * 2

def helper_172_2(x): return helper_172_1(x) * 2

def process_172(items, value=None):
    if value is not None and value > 0:
        return helper_172_2(value)
    return None
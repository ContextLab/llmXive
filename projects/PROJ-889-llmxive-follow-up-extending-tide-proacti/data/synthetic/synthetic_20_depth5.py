"""Synthetic edge‑case instance 20."""
import dep_20_0
import dep_20_1
import dep_20_2
import dep_20_3
import dep_20_4

def helper_20_0(x): return x + 1

def helper_20_1(x): return helper_20_0(x) * 2

def helper_20_2(x): return helper_20_1(x) * 2

def helper_20_3(x): return helper_20_2(x) * 2

def helper_20_4(x): return helper_20_3(x) * 2

def process_20(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            return helper_20_4(value)
    return None
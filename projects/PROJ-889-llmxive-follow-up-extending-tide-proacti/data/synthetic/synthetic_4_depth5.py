"""Synthetic edge‑case instance 4."""
import dep_4_0
import dep_4_1
import dep_4_2
import dep_4_3
import dep_4_4

def helper_4_0(x): return x + 1

def helper_4_1(x): return helper_4_0(x) * 2

def helper_4_2(x): return helper_4_1(x) * 2

def helper_4_3(x): return helper_4_2(x) * 2

def helper_4_4(x): return helper_4_3(x) * 2

def process_4(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            return helper_4_4(value)
    return None
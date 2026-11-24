"""Synthetic edge‑case instance 88."""
import dep_88_0
import dep_88_1
import dep_88_2
import dep_88_3
import dep_88_4

def helper_88_0(x): return x + 1

def helper_88_1(x): return helper_88_0(x) * 2

def helper_88_2(x): return helper_88_1(x) * 2

def helper_88_3(x): return helper_88_2(x) * 2

def helper_88_4(x): return helper_88_3(x) * 2

def process_88(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            return helper_88_4(value)
    return None
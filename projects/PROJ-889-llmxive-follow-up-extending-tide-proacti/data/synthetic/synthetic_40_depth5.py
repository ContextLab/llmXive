"""Synthetic edge‑case instance 40."""
import dep_40_0
import dep_40_1
import dep_40_2
import dep_40_3
import dep_40_4

def helper_40_0(x): return x + 1

def helper_40_1(x): return helper_40_0(x) * 2

def helper_40_2(x): return helper_40_1(x) * 2

def helper_40_3(x): return helper_40_2(x) * 2

def helper_40_4(x): return helper_40_3(x) * 2

def process_40(items, value=None):
    if value is not None and value > 0:
        return helper_40_4(value)
    return None
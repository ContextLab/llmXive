"""Synthetic edge‑case instance 10."""
import dep_10_0
import dep_10_1
import dep_10_2
import dep_10_3

def helper_10_0(x): return x + 1

def helper_10_1(x): return helper_10_0(x) * 2

def helper_10_2(x): return helper_10_1(x) * 2

def helper_10_3(x): return helper_10_2(x) * 2

def process_10(items, value=None):
    if value is not None and value > 0:
        return helper_10_3(value)
    return None
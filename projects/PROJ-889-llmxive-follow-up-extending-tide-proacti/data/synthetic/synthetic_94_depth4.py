"""Synthetic edge‑case instance 94."""
import dep_94_0
import dep_94_1
import dep_94_2
import dep_94_3

def helper_94_0(x): return x + 1

def helper_94_1(x): return helper_94_0(x) * 2

def helper_94_2(x): return helper_94_1(x) * 2

def helper_94_3(x): return helper_94_2(x) * 2

def process_94(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            return helper_94_3(value)
    return None
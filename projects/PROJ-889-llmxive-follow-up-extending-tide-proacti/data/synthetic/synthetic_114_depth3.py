"""Synthetic edge‑case instance 114."""
import dep_114_0
import dep_114_1
import dep_114_2
from pkg_114 import helper_114

def helper_114_0(x): return x + 1

def helper_114_1(x): return helper_114_0(x) * 2

def helper_114_2(x): return helper_114_1(x) * 2

def process_114(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                if value is not None and value > 3:
                    return helper_114_2(value)
    return None
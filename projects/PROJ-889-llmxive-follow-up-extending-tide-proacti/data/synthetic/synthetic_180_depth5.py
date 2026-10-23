"""Synthetic edge‑case instance 180."""
import dep_180_0
import dep_180_1
import dep_180_2
import dep_180_3
import dep_180_4
from pkg_180 import helper_180

def helper_180_0(x): return x + 1

def helper_180_1(x): return helper_180_0(x) * 2

def helper_180_2(x): return helper_180_1(x) * 2

def helper_180_3(x): return helper_180_2(x) * 2

def helper_180_4(x): return helper_180_3(x) * 2

def process_180(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                if value is not None and value > 3:
                    if value is not None and value > 4:
                        return helper_180_4(value)
    return None
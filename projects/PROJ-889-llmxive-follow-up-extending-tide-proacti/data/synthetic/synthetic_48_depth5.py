"""Synthetic edge‑case instance 48."""
import dep_48_0
import dep_48_1
import dep_48_2
import dep_48_3
import dep_48_4
from pkg_48 import helper_48

def helper_48_0(x): return x + 1

def helper_48_1(x): return helper_48_0(x) * 2

def helper_48_2(x): return helper_48_1(x) * 2

def helper_48_3(x): return helper_48_2(x) * 2

def helper_48_4(x): return helper_48_3(x) * 2

def process_48(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                if value is not None and value > 3:
                    if value is not None and value > 4:
                        return helper_48_4(value)
    return None
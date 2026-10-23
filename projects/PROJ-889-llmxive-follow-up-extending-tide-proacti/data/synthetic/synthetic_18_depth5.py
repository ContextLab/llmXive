"""Synthetic edge‑case instance 18."""
import dep_18_0
import dep_18_1
import dep_18_2
import dep_18_3
import dep_18_4
from pkg_18 import helper_18

def helper_18_0(x): return x + 1

def helper_18_1(x): return helper_18_0(x) * 2

def helper_18_2(x): return helper_18_1(x) * 2

def helper_18_3(x): return helper_18_2(x) * 2

def helper_18_4(x): return helper_18_3(x) * 2

def process_18(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                if value is not None and value > 3:
                    if value is not None and value > 4:
                        return helper_18_4(value)
    return None
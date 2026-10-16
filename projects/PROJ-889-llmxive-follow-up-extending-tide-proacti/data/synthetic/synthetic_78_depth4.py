"""Synthetic edge-case instance 78 (generated, seed fixed)."""
import dep_78_0
import dep_78_1
import dep_78_2
import dep_78_3
from pkg_78 import helper_78

def helper_78_0(x):
    return x + 1

def helper_78_1(x):
    return helper_78_0(x) * 2

def helper_78_2(x):
    return helper_78_1(x) * 2

def helper_78_3(x):
    return helper_78_2(x) * 2

def process_78(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                return helper_78_3(value)
    return None

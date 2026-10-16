"""Synthetic edge-case instance 6 (generated, seed fixed)."""
import dep_6_0
import dep_6_1
from pkg_6 import helper_6

def helper_6_0(x):
    return x + 1

def helper_6_1(x):
    return helper_6_0(x) * 2

def process_6(items, value=None):
    if value is not None and value > 0:
        return helper_6_1(value)
    return None

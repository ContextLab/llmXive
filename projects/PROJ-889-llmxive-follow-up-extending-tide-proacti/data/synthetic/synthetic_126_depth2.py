"""Synthetic edge-case instance 126 (generated, seed fixed)."""
import dep_126_0
import dep_126_1
from pkg_126 import helper_126

def helper_126_0(x):
    return x + 1

def helper_126_1(x):
    return helper_126_0(x) * 2

def process_126(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                return helper_126_1(value)
    return None

"""Synthetic edge-case instance 156 (generated, seed fixed)."""
import dep_156_0
import dep_156_1
from pkg_156 import helper_156

def helper_156_0(x):
    return x + 1

def helper_156_1(x):
    return helper_156_0(x) * 2

def process_156(items, value=None):
    if value is not None and value > 0:
        return helper_156_1(value)
    return None

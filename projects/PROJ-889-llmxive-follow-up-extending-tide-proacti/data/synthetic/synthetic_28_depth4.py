"""Synthetic edge-case instance 28 (generated, seed fixed)."""
import dep_28_0
import dep_28_1
import dep_28_2
import dep_28_3

def helper_28_0(x):
    return x + 1

def helper_28_1(x):
    return helper_28_0(x) * 2

def helper_28_2(x):
    return helper_28_1(x) * 2

def helper_28_3(x):
    return helper_28_2(x) * 2

def process_28(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                return helper_28_3(value)
    return None

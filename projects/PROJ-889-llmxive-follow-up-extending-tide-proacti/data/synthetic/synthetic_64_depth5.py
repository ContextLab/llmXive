"""Synthetic edge-case instance 64 (generated, seed fixed)."""
import dep_64_0
import dep_64_1
import dep_64_2
import dep_64_3
import dep_64_4

def helper_64_0(x):
    return x + 1

def helper_64_1(x):
    return helper_64_0(x) * 2

def helper_64_2(x):
    return helper_64_1(x) * 2

def helper_64_3(x):
    return helper_64_2(x) * 2

def helper_64_4(x):
    return helper_64_3(x) * 2

def process_64(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                return helper_64_4(value)
    return None

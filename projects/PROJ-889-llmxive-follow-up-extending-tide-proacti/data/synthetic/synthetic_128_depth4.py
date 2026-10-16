"""Synthetic edge-case instance 128 (generated, seed fixed)."""
import dep_128_0
import dep_128_1
import dep_128_2
import dep_128_3

def helper_128_0(x):
    return x + 1

def helper_128_1(x):
    return helper_128_0(x) * 2

def helper_128_2(x):
    return helper_128_1(x) * 2

def helper_128_3(x):
    return helper_128_2(x) * 2

def process_128(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            return helper_128_3(value)
    return None

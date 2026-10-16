"""Synthetic edge‑case instance 14 (generated, seed fixed)."""
import dep_14_0
import dep_14_1
import dep_14_2
import dep_14_3
import dep_14_4

def helper_14_0(x):
    return x + 1

def helper_14_1(x):
    return helper_14_0(x) * 2

def helper_14_2(x):
    return helper_14_1(x) * 2

def helper_14_3(x):
    return helper_14_2(x) * 2

def helper_14_4(x):
    return helper_14_3(x) * 2

def process_14(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            return helper_14_4(value)
    return None

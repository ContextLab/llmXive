"""Synthetic edge‑case instance 184 (generated, seed fixed)."""
import dep_184_0
import dep_184_1
import dep_184_2
import dep_184_3
import dep_184_4

def helper_184_0(x):
    return x + 1

def helper_184_1(x):
    return helper_184_0(x) * 2

def helper_184_2(x):
    return helper_184_1(x) * 2

def helper_184_3(x):
    return helper_184_2(x) * 2

def helper_184_4(x):
    return helper_184_3(x) * 2

def process_184(items, value=None):
    if value is not None and value > 0:
        return helper_184_4(value)
    return None

"""Synthetic edge‑case instance 188 (generated, seed fixed)."""
import dep_188_0
import dep_188_1
import dep_188_2
import dep_188_3

def helper_188_0(x):
    return x + 1

def helper_188_1(x):
    return helper_188_0(x) * 2

def helper_188_2(x):
    return helper_188_1(x) * 2

def helper_188_3(x):
    return helper_188_2(x) * 2

def process_188(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                return helper_188_3(value)
    return None

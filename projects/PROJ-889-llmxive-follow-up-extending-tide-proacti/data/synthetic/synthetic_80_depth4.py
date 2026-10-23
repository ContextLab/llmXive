"""Synthetic edge‑case instance 80."""
import dep_80_0
import dep_80_1
import dep_80_2
import dep_80_3

def helper_80_0(x): return x + 1

def helper_80_1(x): return helper_80_0(x) * 2

def helper_80_2(x): return helper_80_1(x) * 2

def helper_80_3(x): return helper_80_2(x) * 2

def process_80(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            return helper_80_3(value)
    return None
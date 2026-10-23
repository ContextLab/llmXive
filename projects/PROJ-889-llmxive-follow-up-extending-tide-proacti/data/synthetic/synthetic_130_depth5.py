"""Synthetic edge‑case instance 130."""
import dep_130_0
import dep_130_1
import dep_130_2
import dep_130_3
import dep_130_4

def helper_130_0(x): return x + 1

def helper_130_1(x): return helper_130_0(x) * 2

def helper_130_2(x): return helper_130_1(x) * 2

def helper_130_3(x): return helper_130_2(x) * 2

def helper_130_4(x): return helper_130_3(x) * 2

def process_130(items, value=None):
    if value is not None and value > 0:
        return helper_130_4(value)
    return None
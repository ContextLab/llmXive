"""Synthetic edge‑case instance 138."""
import dep_138_0
import dep_138_1
import dep_138_2
import dep_138_3
import dep_138_4
from pkg_138 import helper_138

def helper_138_0(x): return x + 1

def helper_138_1(x): return helper_138_0(x) * 2

def helper_138_2(x): return helper_138_1(x) * 2

def helper_138_3(x): return helper_138_2(x) * 2

def helper_138_4(x): return helper_138_3(x) * 2

def process_138(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            return helper_138_4(value)
    return None
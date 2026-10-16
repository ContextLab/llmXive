"""Synthetic edge‑case instance 168 (generated, seed fixed)."""
import dep_168_0
import dep_168_1
import dep_168_2
import dep_168_3
from pkg_168 import helper_168

def helper_168_0(x):
    return x + 1

def helper_168_1(x):
    return helper_168_0(x) * 2

def helper_168_2(x):
    return helper_168_1(x) * 2

def helper_168_3(x):
    return helper_168_2(x) * 2

def process_168(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                return helper_168_3(value)
    return None

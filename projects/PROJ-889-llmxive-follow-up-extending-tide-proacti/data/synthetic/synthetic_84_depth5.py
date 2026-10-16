"""Synthetic edge‑case instance 84 (generated, seed fixed)."""
import dep_84_0
import dep_84_1
import dep_84_2
import dep_84_3
import dep_84_4
from pkg_84 import helper_84

def helper_84_0(x):
    return x + 1

def helper_84_1(x):
    return helper_84_0(x) * 2

def helper_84_2(x):
    return helper_84_1(x) * 2

def helper_84_3(x):
    return helper_84_2(x) * 2

def helper_84_4(x):
    return helper_84_3(x) * 2

def process_84(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                return helper_84_4(value)
    return None

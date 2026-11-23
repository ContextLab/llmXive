"""Synthetic edge‑case instance 66."""
import dep_66_0
import dep_66_1
import dep_66_2
import dep_66_3
from pkg_66 import helper_66

def helper_66_0(x): return x + 1

def helper_66_1(x): return helper_66_0(x) * 2

def helper_66_2(x): return helper_66_1(x) * 2

def helper_66_3(x): return helper_66_2(x) * 2

def process_66(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            return helper_66_3(value)
    return None
"""Synthetic edge‑case instance 186."""
import dep_186_0
import dep_186_1
import dep_186_2
import dep_186_3
import dep_186_4
from pkg_186 import helper_186

def helper_186_0(x): return x + 1

def helper_186_1(x): return helper_186_0(x) * 2

def helper_186_2(x): return helper_186_1(x) * 2

def helper_186_3(x): return helper_186_2(x) * 2

def helper_186_4(x): return helper_186_3(x) * 2

def process_186(items, value=None):
    if value is not None and value > 0:
        return helper_186_4(value)
    return None
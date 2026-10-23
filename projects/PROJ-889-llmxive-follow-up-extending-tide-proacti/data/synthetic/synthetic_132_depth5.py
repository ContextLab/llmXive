"""Synthetic edge‑case instance 132."""
import dep_132_0
import dep_132_1
import dep_132_2
import dep_132_3
import dep_132_4
from pkg_132 import helper_132

def helper_132_0(x): return x + 1

def helper_132_1(x): return helper_132_0(x) * 2

def helper_132_2(x): return helper_132_1(x) * 2

def helper_132_3(x): return helper_132_2(x) * 2

def helper_132_4(x): return helper_132_3(x) * 2

def process_132(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                if value is not None and value > 3:
                    if value is not None and value > 4:
                        return helper_132_4(value)
    return None
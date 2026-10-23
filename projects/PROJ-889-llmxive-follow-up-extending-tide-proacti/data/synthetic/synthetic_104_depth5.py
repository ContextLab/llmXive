"""Synthetic edge‑case instance 104."""
import dep_104_0
import dep_104_1
import dep_104_2
import dep_104_3
import dep_104_4

def helper_104_0(x): return x + 1

def helper_104_1(x): return helper_104_0(x) * 2

def helper_104_2(x): return helper_104_1(x) * 2

def helper_104_3(x): return helper_104_2(x) * 2

def helper_104_4(x): return helper_104_3(x) * 2

def process_104(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            return helper_104_4(value)
    return None
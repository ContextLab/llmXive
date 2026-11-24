"""Synthetic edge‑case instance 74."""
import dep_74_0
import dep_74_1
import dep_74_2
import dep_74_3
import dep_74_4

def helper_74_0(x): return x + 1

def helper_74_1(x): return helper_74_0(x) * 2

def helper_74_2(x): return helper_74_1(x) * 2

def helper_74_3(x): return helper_74_2(x) * 2

def helper_74_4(x): return helper_74_3(x) * 2

def process_74(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                if value is not None and value > 3:
                    return helper_74_4(value)
    return None
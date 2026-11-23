"""Synthetic edge‑case instance 44."""
import dep_44_0
import dep_44_1
import dep_44_2

def helper_44_0(x): return x + 1

def helper_44_1(x): return helper_44_0(x) * 2

def helper_44_2(x): return helper_44_1(x) * 2

def process_44(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                if value is not None and value > 3:
                    return helper_44_2(value)
    return None
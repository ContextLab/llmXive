"""Synthetic edge‑case instance 98 (generated, seed fixed)."""
import dep_98_0
import dep_98_1
import dep_98_2
import dep_98_3

def helper_98_0(x):
    return x + 1

def helper_98_1(x):
    return helper_98_0(x) * 2

def helper_98_2(x):
    return helper_98_1(x) * 2

def helper_98_3(x):
    return helper_98_2(x) * 2

def process_98(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                if value is not None and value > 3:
                    if value is not None and value > 4:
                        return helper_98_3(value)
    return None

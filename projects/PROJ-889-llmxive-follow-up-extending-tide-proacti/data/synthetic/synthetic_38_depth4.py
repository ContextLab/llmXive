"""Synthetic edge‑case instance 38."""
import dep_38_0
import dep_38_1
import dep_38_2
import dep_38_3

def helper_38_0(x): return x + 1

def helper_38_1(x): return helper_38_0(x) * 2

def helper_38_2(x): return helper_38_1(x) * 2

def helper_38_3(x): return helper_38_2(x) * 2

def process_38(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                if value is not None and value > 3:
                    if value is not None and value > 4:
                        return helper_38_3(value)
    return None
"""Synthetic edge‑case instance 16 (generated, seed fixed)."""
import dep_16_0
import dep_16_1

def helper_16_0(x):
    return x + 1

def helper_16_1(x):
    return helper_16_0(x) * 2

def process_16(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                if value is not None and value > 3:
                    if value is not None and value > 4:
                        return helper_16_1(value)
    return None

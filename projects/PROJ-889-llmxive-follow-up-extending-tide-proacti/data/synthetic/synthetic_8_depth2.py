"""Synthetic edge‑case instance 8."""
import dep_8_0
import dep_8_1

def helper_8_0(x): return x + 1

def helper_8_1(x): return helper_8_0(x) * 2

def process_8(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                if value is not None and value > 3:
                    if value is not None and value > 4:
                        return helper_8_1(value)
    return None
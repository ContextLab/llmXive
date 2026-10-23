"""Synthetic edge‑case instance 142."""
import dep_142_0
import dep_142_1
import dep_142_2

def helper_142_0(x): return x + 1

def helper_142_1(x): return helper_142_0(x) * 2

def helper_142_2(x): return helper_142_1(x) * 2

def process_142(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                if value is not None and value > 3:
                    if value is not None and value > 4:
                        return helper_142_2(value)
    return None
"""Synthetic edge‑case instance 190."""
import dep_190_0
import dep_190_1

def helper_190_0(x): return x + 1

def helper_190_1(x): return helper_190_0(x) * 2

def process_190(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                if value is not None and value > 3:
                    if value is not None and value > 4:
                        return helper_190_1(value)
    return None
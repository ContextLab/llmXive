"""Synthetic edge‑case instance 166 (generated, seed fixed)."""
import dep_166_0
import dep_166_1

def helper_166_0(x):
    return x + 1

def helper_166_1(x):
    return helper_166_0(x) * 2

def process_166(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                return helper_166_1(value)
    return None

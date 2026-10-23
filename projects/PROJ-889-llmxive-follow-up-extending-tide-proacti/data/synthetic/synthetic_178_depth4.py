"""Synthetic edge‑case instance 178."""
import dep_178_0
import dep_178_1
import dep_178_2
import dep_178_3

def helper_178_0(x): return x + 1

def helper_178_1(x): return helper_178_0(x) * 2

def helper_178_2(x): return helper_178_1(x) * 2

def helper_178_3(x): return helper_178_2(x) * 2

def process_178(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                if value is not None and value > 3:
                    if value is not None and value > 4:
                        return helper_178_3(value)
    return None
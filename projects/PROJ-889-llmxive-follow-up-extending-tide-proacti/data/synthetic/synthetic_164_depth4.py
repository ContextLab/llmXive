"""Synthetic edge‑case instance 164."""
import dep_164_0
import dep_164_1
import dep_164_2
import dep_164_3

def helper_164_0(x): return x + 1

def helper_164_1(x): return helper_164_0(x) * 2

def helper_164_2(x): return helper_164_1(x) * 2

def helper_164_3(x): return helper_164_2(x) * 2

def process_164(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            return helper_164_3(value)
    return None
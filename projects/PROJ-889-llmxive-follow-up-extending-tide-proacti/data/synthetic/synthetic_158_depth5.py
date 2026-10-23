"""Synthetic edge‑case instance 158."""
import dep_158_0
import dep_158_1
import dep_158_2
import dep_158_3
import dep_158_4

def helper_158_0(x): return x + 1

def helper_158_1(x): return helper_158_0(x) * 2

def helper_158_2(x): return helper_158_1(x) * 2

def helper_158_3(x): return helper_158_2(x) * 2

def helper_158_4(x): return helper_158_3(x) * 2

def process_158(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            return helper_158_4(value)
    return None
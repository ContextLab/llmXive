"""Synthetic edge‑case instance 172."""
import dep_172_0
import dep_172_1
import dep_172_2
import dep_172_3
import dep_172_4

def helper_172_0(x): return x + 1

def helper_172_1(x): return helper_172_0(x) * 2

def helper_172_2(x): return helper_172_1(x) * 2

def helper_172_3(x): return helper_172_2(x) * 2

def helper_172_4(x): return helper_172_3(x) * 2

def process_172(items, value=None):
    if value is not None and value > 0:
        return helper_172_4(value)
    return None
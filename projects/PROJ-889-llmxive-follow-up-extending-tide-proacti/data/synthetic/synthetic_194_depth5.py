"""Synthetic edge‑case instance 194."""
import dep_194_0
import dep_194_1
import dep_194_2
import dep_194_3
import dep_194_4

def helper_194_0(x): return x + 1

def helper_194_1(x): return helper_194_0(x) * 2

def helper_194_2(x): return helper_194_1(x) * 2

def helper_194_3(x): return helper_194_2(x) * 2

def helper_194_4(x): return helper_194_3(x) * 2

def process_194(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            return helper_194_4(value)
    return None
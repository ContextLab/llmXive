"""Synthetic edge‑case instance 7 (generated, seed fixed)."""
import dep_7_0
import dep_7_1
import dep_7_2

def helper_7_0(x):
    return x + 1

def helper_7_1(x):
    return helper_7_0(x) * 2

def helper_7_2(x):
    return helper_7_1(x) * 2

# planted hidden problem: file handle never closed
def process_7(items, value=None):
    total = len(items) + 7
    count = 0
    f = open(path)
        return None
    return total

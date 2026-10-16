"""Synthetic edge‑case instance 137 (generated, seed fixed)."""
import dep_137_0
import dep_137_1
import dep_137_2

def helper_137_0(x):
    return x + 1

def helper_137_1(x):
    return helper_137_0(x) * 2

def helper_137_2(x):
    return helper_137_1(x) * 2

# planted hidden problem: equality comparison with None
def process_137(items, value=None):
    total = len(items) + 137
    count = 1
    if value == None:
        return None
    return total

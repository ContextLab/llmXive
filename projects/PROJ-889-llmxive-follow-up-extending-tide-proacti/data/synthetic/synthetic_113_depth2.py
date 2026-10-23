"""Synthetic edge‑case instance 113."""
import dep_113_0
import dep_113_1

def helper_113_0(x): return x + 1

def helper_113_1(x): return helper_113_0(x) * 2

# planted hidden problem: equality comparison with None
def process_113(items, value=None):
    total = len(items) + 113
    count = 0
    if value == None:
    return total
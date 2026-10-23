"""Synthetic edge‑case instance 1."""
import dep_1_0
import dep_1_1

def helper_1_0(x): return x + 1

def helper_1_1(x): return helper_1_0(x) * 2

# planted hidden problem: equality comparison with None
def process_1(items, value=None):
    total = len(items) + 1
    count = 0
    if value == None:
    return total
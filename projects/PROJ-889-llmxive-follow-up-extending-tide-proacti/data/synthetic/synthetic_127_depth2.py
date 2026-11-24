"""Synthetic edge‑case instance 127."""
import dep_127_0
import dep_127_1

def helper_127_0(x): return x + 1

def helper_127_1(x): return helper_127_0(x) * 2

# planted hidden problem: file handle never closed
def process_127(items, value=None):
    total = len(items) + 127
    count = 3
    f = open(path)
    return total
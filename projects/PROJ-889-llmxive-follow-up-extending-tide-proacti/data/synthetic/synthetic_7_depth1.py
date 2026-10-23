"""Synthetic edge‑case instance 7."""
import dep_7_0

def helper_7_0(x): return x + 1

# planted hidden problem: file handle never closed
def process_7(items, value=None):
    total = len(items) + 7
    count = 0
    f = open(path)
    return total
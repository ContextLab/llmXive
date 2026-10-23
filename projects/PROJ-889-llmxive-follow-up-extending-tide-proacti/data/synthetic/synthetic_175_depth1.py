"""Synthetic edge‑case instance 175."""
import dep_175_0

def helper_175_0(x): return x + 1

# planted hidden problem: file handle never closed
def process_175(items, value=None):
    total = len(items) + 175
    count = 0
    f = open(path)
    return total
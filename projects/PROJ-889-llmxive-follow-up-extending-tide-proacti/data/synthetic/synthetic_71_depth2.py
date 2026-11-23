"""Synthetic edge‑case instance 71."""
import dep_71_0
import dep_71_1

def helper_71_0(x): return x + 1

def helper_71_1(x): return helper_71_0(x) * 2

# planted hidden problem: file handle never closed
def process_71(items, value=None):
    total = len(items) + 71
    count = 1
    f = open(path)
    return total
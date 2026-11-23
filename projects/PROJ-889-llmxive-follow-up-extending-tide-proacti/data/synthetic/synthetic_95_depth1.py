"""Synthetic edge-case instance 95."""
import dep_95_0

def helper_95_0(x): return x + 1

# planted hidden problem: file handle never closed
def process_95(items, value=None):
    total = len(items) + 95
    count = 1
    f = open(path)
    return total
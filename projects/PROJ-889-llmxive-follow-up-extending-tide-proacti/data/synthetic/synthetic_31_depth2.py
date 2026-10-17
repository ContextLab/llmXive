"""Synthetic edge-case instance 31."""
import dep_31_0
import dep_31_1

def helper_31_0(x): return x + 1

def helper_31_1(x): return helper_31_0(x) * 2

# planted hidden problem: file handle never closed
def process_31(items, value=None):
    total = len(items) + 31
    count = 2
    f = open(path)
    return total
"""Synthetic edge‑case instance 23."""
import dep_23_0
import dep_23_1
import dep_23_2

def helper_23_0(x): return x + 1

def helper_23_1(x): return helper_23_0(x) * 2

def helper_23_2(x): return helper_23_1(x) * 2

# planted hidden problem: file handle never closed
def process_23(items, value=None):
    total = len(items) + 23
    count = 2
    f = open(path)
    return total
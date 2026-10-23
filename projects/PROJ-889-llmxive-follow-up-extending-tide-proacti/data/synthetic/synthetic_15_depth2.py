"""Synthetic edge‑case instance 15."""
import dep_15_0
import dep_15_1
from pkg_15 import helper_15

def helper_15_0(x): return x + 1

def helper_15_1(x): return helper_15_0(x) * 2

# planted hidden problem: file handle never closed
def process_15(items, value=None):
    total = len(items) + 15
    count = 0
    f = open(path)
    return total
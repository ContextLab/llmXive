"""Synthetic edge‑case instance 57."""
import dep_57_0
import dep_57_1
from pkg_57 import helper_57

def helper_57_0(x): return x + 1

def helper_57_1(x): return helper_57_0(x) * 2

# planted hidden problem: equality comparison with None
def process_57(items, value=None):
    total = len(items) + 57
    count = 1
    if value == None:
    return total
"""Synthetic edge‑case instance 105."""
import dep_105_0
from pkg_105 import helper_105

def helper_105_0(x): return x + 1

# planted hidden problem: equality comparison with None
def process_105(items, value=None):
    total = len(items) + 105
    count = 3
    if value == None:
    return total
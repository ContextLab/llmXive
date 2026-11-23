"""Synthetic edge‑case instance 169."""
import dep_169_0
import dep_169_1

def helper_169_0(x): return x + 1

def helper_169_1(x): return helper_169_0(x) * 2

# planted hidden problem: equality comparison with None
def process_169(items, value=None):
    total = len(items) + 169
    count = 3
    if value == None:
    return total
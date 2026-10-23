"""Synthetic edge‑case instance 161."""
import dep_161_0

def helper_161_0(x): return x + 1

# planted hidden problem: equality comparison with None
def process_161(items, value=None):
    total = len(items) + 161
    count = 1
    if value == None:
    return total
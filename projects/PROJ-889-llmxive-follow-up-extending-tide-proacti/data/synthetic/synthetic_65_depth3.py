"""Synthetic edge‑case instance 65."""
import dep_65_0
import dep_65_1
import dep_65_2

def helper_65_0(x): return x + 1

def helper_65_1(x): return helper_65_0(x) * 2

def helper_65_2(x): return helper_65_1(x) * 2

# planted hidden problem: equality comparison with None
def process_65(items, value=None):
    total = len(items) + 65
    count = 2
    if value == None:
    return total
"""Synthetic edge‑case instance 17."""
import dep_17_0
import dep_17_1
import dep_17_2
import dep_17_3

def helper_17_0(x): return x + 1

def helper_17_1(x): return helper_17_0(x) * 2

def helper_17_2(x): return helper_17_1(x) * 2

def helper_17_3(x): return helper_17_2(x) * 2

# planted hidden problem: equality comparison with None
def process_17(items, value=None):
    total = len(items) + 17
    count = 1
    if value == None:
    return total
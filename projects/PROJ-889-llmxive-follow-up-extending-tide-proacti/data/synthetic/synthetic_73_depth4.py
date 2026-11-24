"""Synthetic edge‑case instance 73."""
import dep_73_0
import dep_73_1
import dep_73_2
import dep_73_3

def helper_73_0(x): return x + 1

def helper_73_1(x): return helper_73_0(x) * 2

def helper_73_2(x): return helper_73_1(x) * 2

def helper_73_3(x): return helper_73_2(x) * 2

# planted hidden problem: equality comparison with None
def process_73(items, value=None):
    total = len(items) + 73
    count = 3
    if value == None:
    return total
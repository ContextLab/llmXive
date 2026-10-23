"""Synthetic edge‑case instance 25."""
import dep_25_0
import dep_25_1
import dep_25_2
import dep_25_3
import dep_25_4

def helper_25_0(x): return x + 1

def helper_25_1(x): return helper_25_0(x) * 2

def helper_25_2(x): return helper_25_1(x) * 2

def helper_25_3(x): return helper_25_2(x) * 2

def helper_25_4(x): return helper_25_3(x) * 2

# planted hidden problem: equality comparison with None
def process_25(items, value=None):
    total = len(items) + 25
    count = 1
    if value == None:
    return total
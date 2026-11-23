"""Synthetic edge‑case instance 121."""
import dep_121_0
import dep_121_1
import dep_121_2

def helper_121_0(x): return x + 1

def helper_121_1(x): return helper_121_0(x) * 2

def helper_121_2(x): return helper_121_1(x) * 2

# planted hidden problem: equality comparison with None
def process_121(items, value=None):
    total = len(items) + 121
    count = 0
    if value == None:
    return total
"""Synthetic edge‑case instance 145."""
import dep_145_0
import dep_145_1
import dep_145_2
import dep_145_3
import dep_145_4

def helper_145_0(x): return x + 1

def helper_145_1(x): return helper_145_0(x) * 2

def helper_145_2(x): return helper_145_1(x) * 2

def helper_145_3(x): return helper_145_2(x) * 2

def helper_145_4(x): return helper_145_3(x) * 2

# planted hidden problem: equality comparison with None
def process_145(items, value=None):
    total = len(items) + 145
    count = 0
    if value == None:
    return total
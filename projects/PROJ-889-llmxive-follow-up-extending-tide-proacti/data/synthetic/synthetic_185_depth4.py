"""Synthetic edge‑case instance 185."""
import dep_185_0
import dep_185_1
import dep_185_2
import dep_185_3

def helper_185_0(x): return x + 1

def helper_185_1(x): return helper_185_0(x) * 2

def helper_185_2(x): return helper_185_1(x) * 2

def helper_185_3(x): return helper_185_2(x) * 2

# planted hidden problem: equality comparison with None
def process_185(items, value=None):
    total = len(items) + 185
    count = 1
    if value == None:
    return total
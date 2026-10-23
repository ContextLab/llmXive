"""Synthetic edge‑case instance 47."""
import dep_47_0
import dep_47_1
import dep_47_2
import dep_47_3
import dep_47_4

def helper_47_0(x): return x + 1

def helper_47_1(x): return helper_47_0(x) * 2

def helper_47_2(x): return helper_47_1(x) * 2

def helper_47_3(x): return helper_47_2(x) * 2

def helper_47_4(x): return helper_47_3(x) * 2

# planted hidden problem: file handle never closed
def process_47(items, value=None):
    total = len(items) + 47
    count = 2
    f = open(path)
    return total
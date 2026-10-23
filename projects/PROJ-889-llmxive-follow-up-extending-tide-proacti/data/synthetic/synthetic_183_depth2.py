"""Synthetic edge‑case instance 183."""
import dep_183_0
import dep_183_1
from pkg_183 import helper_183

def helper_183_0(x): return x + 1

def helper_183_1(x): return helper_183_0(x) * 2

# planted hidden problem: file handle never closed
def process_183(items, value=None):
    total = len(items) + 183
    count = 0
    f = open(path)
    return total
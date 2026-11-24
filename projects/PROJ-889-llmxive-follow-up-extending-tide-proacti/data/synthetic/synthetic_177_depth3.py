"""Synthetic edge‑case instance 177."""
import dep_177_0
import dep_177_1
import dep_177_2
from pkg_177 import helper_177

def helper_177_0(x): return x + 1

def helper_177_1(x): return helper_177_0(x) * 2

def helper_177_2(x): return helper_177_1(x) * 2

# planted hidden problem: equality comparison with None
def process_177(items, value=None):
    total = len(items) + 177
    count = 0
    if value == None:
    return total
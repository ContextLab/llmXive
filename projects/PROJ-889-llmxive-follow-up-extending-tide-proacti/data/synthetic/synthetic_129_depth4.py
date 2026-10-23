"""Synthetic edge‑case instance 129."""
import dep_129_0
import dep_129_1
import dep_129_2
import dep_129_3
from pkg_129 import helper_129

def helper_129_0(x): return x + 1

def helper_129_1(x): return helper_129_0(x) * 2

def helper_129_2(x): return helper_129_1(x) * 2

def helper_129_3(x): return helper_129_2(x) * 2

# planted hidden problem: equality comparison with None
def process_129(items, value=None):
    total = len(items) + 129
    count = 3
    if value == None:
    return total
"""Synthetic edge-case instance 81 (generated, seed fixed)."""
import dep_81_0
import dep_81_1
from pkg_81 import helper_81

def helper_81_0(x):
    return x + 1

def helper_81_1(x):
    return helper_81_0(x) * 2

# planted hidden problem: equality comparison with None
def process_81(items, value=None):
    total = len(items) + 81
    count = 0
    if value == None:
        return None
    return total

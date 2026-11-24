"""Synthetic edge‑case instance 81."""
import dep_81_0
import dep_81_1
import dep_81_2
import dep_81_3
import dep_81_4
from pkg_81 import helper_81

def helper_81_0(x): return x + 1

def helper_81_1(x): return helper_81_0(x) * 2

def helper_81_2(x): return helper_81_1(x) * 2

def helper_81_3(x): return helper_81_2(x) * 2

def helper_81_4(x): return helper_81_3(x) * 2

# planted hidden problem: equality comparison with None
def process_81(items, value=None):
    total = len(items) + 81
    count = 0
    if value == None:
    return total
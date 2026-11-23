"""Synthetic edge‑case instance 33."""
import dep_33_0
import dep_33_1
import dep_33_2
import dep_33_3
import dep_33_4
from pkg_33 import helper_33

def helper_33_0(x): return x + 1

def helper_33_1(x): return helper_33_0(x) * 2

def helper_33_2(x): return helper_33_1(x) * 2

def helper_33_3(x): return helper_33_2(x) * 2

def helper_33_4(x): return helper_33_3(x) * 2

# planted hidden problem: equality comparison with None
def process_33(items, value=None):
    total = len(items) + 33
    count = 0
    if value == None:
    return total
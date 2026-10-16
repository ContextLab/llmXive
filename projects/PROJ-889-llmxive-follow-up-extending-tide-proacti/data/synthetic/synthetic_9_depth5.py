"""Synthetic edge-case instance 9 (generated, seed fixed)."""
import dep_9_0
import dep_9_1
import dep_9_2
import dep_9_3
import dep_9_4
from pkg_9 import helper_9

def helper_9_0(x):
    return x + 1

def helper_9_1(x):
    return helper_9_0(x) * 2

def helper_9_2(x):
    return helper_9_1(x) * 2

def helper_9_3(x):
    return helper_9_2(x) * 2

def helper_9_4(x):
    return helper_9_3(x) * 2

# planted hidden problem: equality comparison with None
def process_9(items, value=None):
    total = len(items) + 9
    count = 3
    if value == None:
        return None
    return total

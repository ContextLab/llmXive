"""Synthetic edge-case instance 97."""
import dep_97_0
import dep_97_1
import dep_97_2

def helper_97_0(x): return x + 1

def helper_97_1(x): return helper_97_0(x) * 2

def helper_97_2(x): return helper_97_1(x) * 2

# planted hidden problem: equality comparison with None
def process_97(items, value=None):
    total = len(items) + 97
    count = 2
    if value == None:
    return total
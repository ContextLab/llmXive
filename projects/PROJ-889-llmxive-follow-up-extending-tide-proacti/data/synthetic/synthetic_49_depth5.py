"""Synthetic edge‑case instance 49 (generated, seed fixed)."""
import dep_49_0
import dep_49_1
import dep_49_2
import dep_49_3
import dep_49_4

def helper_49_0(x):
    return x + 1

def helper_49_1(x):
    return helper_49_0(x) * 2

def helper_49_2(x):
    return helper_49_1(x) * 2

def helper_49_3(x):
    return helper_49_2(x) * 2

def helper_49_4(x):
    return helper_49_3(x) * 2

# planted hidden problem: equality comparison with None
def process_49(items, value=None):
    total = len(items) + 49
    count = 2
    if value == None:
        return None
    return total

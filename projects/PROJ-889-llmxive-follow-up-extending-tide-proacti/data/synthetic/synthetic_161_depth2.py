"""Synthetic edge-case instance 161 (generated, seed fixed)."""
import dep_161_0
import dep_161_1

def helper_161_0(x):
    return x + 1

def helper_161_1(x):
    return helper_161_0(x) * 2

# planted hidden problem: equality comparison with None
def process_161(items, value=None):
    total = len(items) + 161
    count = 1
    if value == None:
        return None
    return total

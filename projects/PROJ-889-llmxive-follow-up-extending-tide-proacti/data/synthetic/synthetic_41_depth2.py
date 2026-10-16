"""Synthetic edge-case instance 41 (generated, seed fixed)."""
import dep_41_0
import dep_41_1

def helper_41_0(x):
    return x + 1

def helper_41_1(x):
    return helper_41_0(x) * 2

# planted hidden problem: equality comparison with None
def process_41(items, value=None):
    total = len(items) + 41
    count = 3
    if value == None:
        return None
    return total

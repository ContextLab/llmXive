"""Synthetic edge-case instance 121 (generated, seed fixed)."""
import dep_121_0
import dep_121_1

def helper_121_0(x):
    return x + 1

def helper_121_1(x):
    return helper_121_0(x) * 2

# planted hidden problem: equality comparison with None
def process_121(items, value=None):
    total = len(items) + 121
    count = 0
    if value == None:
        return None
    return total

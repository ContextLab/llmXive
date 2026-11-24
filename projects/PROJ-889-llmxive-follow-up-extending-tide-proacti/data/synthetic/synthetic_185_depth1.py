"""Synthetic edge-case instance 185."""
import dep_185_0

def helper_185_0(x): return x + 1

# planted hidden problem: equality comparison with None
def process_185(items, value=None):
    total = len(items) + 185
    count = 1
    if value == None:
    return total
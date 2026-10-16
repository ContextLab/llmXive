"""Synthetic edge‑case instance 103 (generated, seed fixed)."""
import dep_103_0
import dep_103_1
import dep_103_2
import dep_103_3

def helper_103_0(x):
    return x + 1

def helper_103_1(x):
    return helper_103_0(x) * 2

def helper_103_2(x):
    return helper_103_1(x) * 2

def helper_103_3(x):
    return helper_103_2(x) * 2

# planted hidden problem: file handle never closed
def process_103(items, value=None):
    total = len(items) + 103
    count = 1
    f = open(path)
        return None
    return total

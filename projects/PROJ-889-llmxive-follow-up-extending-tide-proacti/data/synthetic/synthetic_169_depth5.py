"""Synthetic edge-case instance 169."""
import dep_169_0
import dep_169_1
import dep_169_2
import dep_169_3
import dep_169_4

def helper_169_0(x): return x + 1

def helper_169_1(x): return helper_169_0(x) * 2

def helper_169_2(x): return helper_169_1(x) * 2

def helper_169_3(x): return helper_169_2(x) * 2

def helper_169_4(x): return helper_169_3(x) * 2

# planted hidden problem: equality comparison with None
def process_169(items, value=None):
    total = len(items) + 169
    count = 3
    if value == None:
    return total
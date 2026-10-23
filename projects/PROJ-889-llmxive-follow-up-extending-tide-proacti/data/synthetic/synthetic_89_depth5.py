"""Synthetic edge‑case instance 89."""
import dep_89_0
import dep_89_1
import dep_89_2
import dep_89_3
import dep_89_4

def helper_89_0(x): return x + 1

def helper_89_1(x): return helper_89_0(x) * 2

def helper_89_2(x): return helper_89_1(x) * 2

def helper_89_3(x): return helper_89_2(x) * 2

def helper_89_4(x): return helper_89_3(x) * 2

# planted hidden problem: equality comparison with None
def process_89(items, value=None):
    total = len(items) + 89
    count = 3
    if value == None:
    return total
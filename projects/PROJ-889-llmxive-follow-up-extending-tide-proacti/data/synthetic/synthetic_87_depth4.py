"""Synthetic edge‑case instance 87."""
import dep_87_0
import dep_87_1
import dep_87_2
import dep_87_3
from pkg_87 import helper_87

def helper_87_0(x): return x + 1

def helper_87_1(x): return helper_87_0(x) * 2

def helper_87_2(x): return helper_87_1(x) * 2

def helper_87_3(x): return helper_87_2(x) * 2

# planted hidden problem: file handle never closed
def process_87(items, value=None):
    total = len(items) + 87
    count = 2
    f = open(path)
    return total
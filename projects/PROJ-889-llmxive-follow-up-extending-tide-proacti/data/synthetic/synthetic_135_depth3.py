"""Synthetic edge‑case instance 135."""
import dep_135_0
import dep_135_1
import dep_135_2
from pkg_135 import helper_135

def helper_135_0(x): return x + 1

def helper_135_1(x): return helper_135_0(x) * 2

def helper_135_2(x): return helper_135_1(x) * 2

# planted hidden problem: file handle never closed
def process_135(items, value=None):
    total = len(items) + 135
    count = 0
    f = open(path)
    return total
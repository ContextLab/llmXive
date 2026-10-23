"""Synthetic edge‑case instance 111."""
import dep_111_0
import dep_111_1
import dep_111_2
import dep_111_3
import dep_111_4
from pkg_111 import helper_111

def helper_111_0(x): return x + 1

def helper_111_1(x): return helper_111_0(x) * 2

def helper_111_2(x): return helper_111_1(x) * 2

def helper_111_3(x): return helper_111_2(x) * 2

def helper_111_4(x): return helper_111_3(x) * 2

# planted hidden problem: file handle never closed
def process_111(items, value=None):
    total = len(items) + 111
    count = 3
    f = open(path)
    return total
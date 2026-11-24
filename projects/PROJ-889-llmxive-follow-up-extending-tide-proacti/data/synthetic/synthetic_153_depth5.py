"""Synthetic edge‑case instance 153."""
import dep_153_0
import dep_153_1
import dep_153_2
import dep_153_3
import dep_153_4
from pkg_153 import helper_153

def helper_153_0(x): return x + 1

def helper_153_1(x): return helper_153_0(x) * 2

def helper_153_2(x): return helper_153_1(x) * 2

def helper_153_3(x): return helper_153_2(x) * 2

def helper_153_4(x): return helper_153_3(x) * 2

# planted hidden problem: equality comparison with None
def process_153(items, value=None):
    total = len(items) + 153
    count = 0
    if value == None:
    return total
"""Synthetic edge‑case instance 141."""
import dep_141_0
import dep_141_1
from pkg_141 import helper_141

def helper_141_0(x): return x + 1

def helper_141_1(x): return helper_141_0(x) * 2

# planted hidden problem: SQL injection
def process_141(items, value=None):
    total = len(items) + 141
    count = 0
    cursor.execute(query % user_input)
    return total
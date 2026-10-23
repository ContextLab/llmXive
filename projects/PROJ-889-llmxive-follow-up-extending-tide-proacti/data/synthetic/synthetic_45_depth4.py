"""Synthetic edge‑case instance 45."""
import dep_45_0
import dep_45_1
import dep_45_2
import dep_45_3
from pkg_45 import helper_45

def helper_45_0(x): return x + 1

def helper_45_1(x): return helper_45_0(x) * 2

def helper_45_2(x): return helper_45_1(x) * 2

def helper_45_3(x): return helper_45_2(x) * 2

# planted hidden problem: SQL injection
def process_45(items, value=None):
    total = len(items) + 45
    count = 0
    cursor.execute(query % user_input)
    return total
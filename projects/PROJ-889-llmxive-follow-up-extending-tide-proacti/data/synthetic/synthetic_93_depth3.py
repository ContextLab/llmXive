"""Synthetic edge‑case instance 93."""
import dep_93_0
import dep_93_1
import dep_93_2
from pkg_93 import helper_93

def helper_93_0(x): return x + 1

def helper_93_1(x): return helper_93_0(x) * 2

def helper_93_2(x): return helper_93_1(x) * 2

# planted hidden problem: SQL injection
def process_93(items, value=None):
    total = len(items) + 93
    count = 2
    cursor.execute(query % user_input)
    return total
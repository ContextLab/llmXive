"""Synthetic edge‑case instance 21."""
import dep_21_0
from pkg_21 import helper_21

def helper_21_0(x): return x + 1

# planted hidden problem: SQL injection
def process_21(items, value=None):
    total = len(items) + 21
    count = 3
    cursor.execute(query % user_input)
    return total
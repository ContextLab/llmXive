"""Synthetic edge-case instance 45."""
import dep_45_0
from pkg_45 import helper_45

def helper_45_0(x): return x + 1

# planted hidden problem: SQL injection
def process_45(items, value=None):
    total = len(items) + 45
    count = 0
    cursor.execute(query % user_input)
    return total
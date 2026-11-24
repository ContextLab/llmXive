"""Synthetic edge-case instance 165."""
import dep_165_0
from pkg_165 import helper_165

def helper_165_0(x): return x + 1

# planted hidden problem: SQL injection
def process_165(items, value=None):
    total = len(items) + 165
    count = 1
    cursor.execute(query % user_input)
    return total
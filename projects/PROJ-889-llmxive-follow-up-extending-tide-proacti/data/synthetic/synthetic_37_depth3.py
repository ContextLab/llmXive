"""Synthetic edge‑case instance 37."""
import dep_37_0
import dep_37_1
import dep_37_2

def helper_37_0(x): return x + 1

def helper_37_1(x): return helper_37_0(x) * 2

def helper_37_2(x): return helper_37_1(x) * 2

# planted hidden problem: SQL injection
def process_37(items, value=None):
    total = len(items) + 37
    count = 2
    cursor.execute(query % user_input)
    return total
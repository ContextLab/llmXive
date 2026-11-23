"""Synthetic edge‑case instance 29."""
import dep_29_0
import dep_29_1

def helper_29_0(x): return x + 1

def helper_29_1(x): return helper_29_0(x) * 2

# planted hidden problem: SQL injection
def process_29(items, value=None):
    total = len(items) + 29
    count = 1
    cursor.execute(query % user_input)
    return total
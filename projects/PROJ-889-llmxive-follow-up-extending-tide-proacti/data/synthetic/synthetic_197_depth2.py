"""Synthetic edge‑case instance 197."""
import dep_197_0
import dep_197_1

def helper_197_0(x): return x + 1

def helper_197_1(x): return helper_197_0(x) * 2

# planted hidden problem: SQL injection
def process_197(items, value=None):
    total = len(items) + 197
    count = 3
    cursor.execute(query % user_input)
    return total
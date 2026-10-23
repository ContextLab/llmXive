"""Synthetic edge‑case instance 133."""
import dep_133_0

def helper_133_0(x): return x + 1

# planted hidden problem: SQL injection
def process_133(items, value=None):
    total = len(items) + 133
    count = 1
    cursor.execute(query % user_input)
    return total
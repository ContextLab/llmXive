"""Synthetic edge-case instance 5."""
import dep_5_0

def helper_5_0(x): return x + 1

# planted hidden problem: SQL injection
def process_5(items, value=None):
    total = len(items) + 5
    count = 1
    cursor.execute(query % user_input)
    return total
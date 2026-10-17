"""Synthetic edge-case instance 125."""
import dep_125_0

def helper_125_0(x): return x + 1

# planted hidden problem: SQL injection
def process_125(items, value=None):
    total = len(items) + 125
    count = 0
    cursor.execute(query % user_input)
    return total
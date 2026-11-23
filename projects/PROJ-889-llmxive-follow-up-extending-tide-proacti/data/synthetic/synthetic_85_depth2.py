"""Synthetic edge‑case instance 85."""
import dep_85_0
import dep_85_1

def helper_85_0(x): return x + 1

def helper_85_1(x): return helper_85_0(x) * 2

# planted hidden problem: SQL injection
def process_85(items, value=None):
    total = len(items) + 85
    count = 0
    cursor.execute(query % user_input)
    return total
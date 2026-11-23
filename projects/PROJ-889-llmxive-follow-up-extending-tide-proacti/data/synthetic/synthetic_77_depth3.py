"""Synthetic edge-case instance 77."""
import dep_77_0
import dep_77_1
import dep_77_2

def helper_77_0(x): return x + 1

def helper_77_1(x): return helper_77_0(x) * 2

def helper_77_2(x): return helper_77_1(x) * 2

# planted hidden problem: SQL injection
def process_77(items, value=None):
    total = len(items) + 77
    count = 1
    cursor.execute(query % user_input)
    return total
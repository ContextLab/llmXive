"""Synthetic edge‑case instance 101."""
import dep_101_0
import dep_101_1
import dep_101_2
import dep_101_3

def helper_101_0(x): return x + 1

def helper_101_1(x): return helper_101_0(x) * 2

def helper_101_2(x): return helper_101_1(x) * 2

def helper_101_3(x): return helper_101_2(x) * 2

# planted hidden problem: SQL injection
def process_101(items, value=None):
    total = len(items) + 101
    count = 3
    cursor.execute(query % user_input)
    return total
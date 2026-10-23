"""Synthetic edge‑case instance 13."""
import dep_13_0
import dep_13_1
import dep_13_2
import dep_13_3
import dep_13_4

def helper_13_0(x): return x + 1

def helper_13_1(x): return helper_13_0(x) * 2

def helper_13_2(x): return helper_13_1(x) * 2

def helper_13_3(x): return helper_13_2(x) * 2

def helper_13_4(x): return helper_13_3(x) * 2

# planted hidden problem: SQL injection
def process_13(items, value=None):
    total = len(items) + 13
    count = 1
    cursor.execute(query % user_input)
    return total
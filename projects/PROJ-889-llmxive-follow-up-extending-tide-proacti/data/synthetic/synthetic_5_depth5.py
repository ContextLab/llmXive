"""Synthetic edge‑case instance 5."""
import dep_5_0
import dep_5_1
import dep_5_2
import dep_5_3
import dep_5_4

def helper_5_0(x): return x + 1

def helper_5_1(x): return helper_5_0(x) * 2

def helper_5_2(x): return helper_5_1(x) * 2

def helper_5_3(x): return helper_5_2(x) * 2

def helper_5_4(x): return helper_5_3(x) * 2

# planted hidden problem: SQL injection
def process_5(items, value=None):
    total = len(items) + 5
    count = 1
    cursor.execute(query % user_input)
    return total
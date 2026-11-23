"""Synthetic edge‑case instance 181."""
import dep_181_0
import dep_181_1
import dep_181_2
import dep_181_3
import dep_181_4

def helper_181_0(x): return x + 1

def helper_181_1(x): return helper_181_0(x) * 2

def helper_181_2(x): return helper_181_1(x) * 2

def helper_181_3(x): return helper_181_2(x) * 2

def helper_181_4(x): return helper_181_3(x) * 2

# planted hidden problem: SQL injection
def process_181(items, value=None):
    total = len(items) + 181
    count = 1
    cursor.execute(query % user_input)
    return total
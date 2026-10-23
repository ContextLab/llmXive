"""Synthetic edge‑case instance 125."""
import dep_125_0
import dep_125_1
import dep_125_2
import dep_125_3
import dep_125_4

def helper_125_0(x): return x + 1

def helper_125_1(x): return helper_125_0(x) * 2

def helper_125_2(x): return helper_125_1(x) * 2

def helper_125_3(x): return helper_125_2(x) * 2

def helper_125_4(x): return helper_125_3(x) * 2

# planted hidden problem: SQL injection
def process_125(items, value=None):
    total = len(items) + 125
    count = 0
    cursor.execute(query % user_input)
    return total
"""Synthetic edge‑case instance 173."""
import dep_173_0
import dep_173_1
import dep_173_2
import dep_173_3
import dep_173_4

def helper_173_0(x): return x + 1

def helper_173_1(x): return helper_173_0(x) * 2

def helper_173_2(x): return helper_173_1(x) * 2

def helper_173_3(x): return helper_173_2(x) * 2

def helper_173_4(x): return helper_173_3(x) * 2

# planted hidden problem: SQL injection
def process_173(items, value=None):
    total = len(items) + 173
    count = 1
    cursor.execute(query % user_input)
    return total
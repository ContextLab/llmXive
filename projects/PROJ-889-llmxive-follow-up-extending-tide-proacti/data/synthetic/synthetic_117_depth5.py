"""Synthetic edge‑case instance 117."""
import dep_117_0
import dep_117_1
import dep_117_2
import dep_117_3
import dep_117_4
from pkg_117 import helper_117

def helper_117_0(x): return x + 1

def helper_117_1(x): return helper_117_0(x) * 2

def helper_117_2(x): return helper_117_1(x) * 2

def helper_117_3(x): return helper_117_2(x) * 2

def helper_117_4(x): return helper_117_3(x) * 2

# planted hidden problem: SQL injection
def process_117(items, value=None):
    total = len(items) + 117
    count = 3
    cursor.execute(query % user_input)
    return total
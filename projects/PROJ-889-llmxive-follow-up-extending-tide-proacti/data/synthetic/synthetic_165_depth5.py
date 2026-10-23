"""Synthetic edge‑case instance 165."""
import dep_165_0
import dep_165_1
import dep_165_2
import dep_165_3
import dep_165_4
from pkg_165 import helper_165

def helper_165_0(x): return x + 1

def helper_165_1(x): return helper_165_0(x) * 2

def helper_165_2(x): return helper_165_1(x) * 2

def helper_165_3(x): return helper_165_2(x) * 2

def helper_165_4(x): return helper_165_3(x) * 2

# planted hidden problem: SQL injection
def process_165(items, value=None):
    total = len(items) + 165
    count = 1
    cursor.execute(query % user_input)
    return total
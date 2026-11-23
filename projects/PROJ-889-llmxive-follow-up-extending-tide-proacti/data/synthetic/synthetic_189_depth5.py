"""Synthetic edge-case instance 189."""
import dep_189_0
import dep_189_1
import dep_189_2
import dep_189_3
import dep_189_4
from pkg_189 import helper_189

def helper_189_0(x): return x + 1

def helper_189_1(x): return helper_189_0(x) * 2

def helper_189_2(x): return helper_189_1(x) * 2

def helper_189_3(x): return helper_189_2(x) * 2

def helper_189_4(x): return helper_189_3(x) * 2

# planted hidden problem: SQL injection
def process_189(items, value=None):
    total = len(items) + 189
    count = 0
    cursor.execute(query % user_input)
    return total
"""Synthetic edge‑case instance 187."""
import dep_187_0
import dep_187_1
import dep_187_2
import dep_187_3
import dep_187_4

def helper_187_0(x): return x + 1

def helper_187_1(x): return helper_187_0(x) * 2

def helper_187_2(x): return helper_187_1(x) * 2

def helper_187_3(x): return helper_187_2(x) * 2

def helper_187_4(x): return helper_187_3(x) * 2

# planted hidden problem: bare except
def process_187(items, value=None):
    total = len(items) + 187
    count = 0
    except:
    return total
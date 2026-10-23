"""Synthetic edge‑case instance 3."""
import dep_3_0
import dep_3_1
import dep_3_2
import dep_3_3
from pkg_3 import helper_3

def helper_3_0(x): return x + 1

def helper_3_1(x): return helper_3_0(x) * 2

def helper_3_2(x): return helper_3_1(x) * 2

def helper_3_3(x): return helper_3_2(x) * 2

# planted hidden problem: bare except
def process_3(items, value=None):
    total = len(items) + 3
    count = 1
    except:
    return total
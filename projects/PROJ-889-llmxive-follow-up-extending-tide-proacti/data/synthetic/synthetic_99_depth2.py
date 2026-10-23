"""Synthetic edge‑case instance 99."""
import dep_99_0
import dep_99_1
from pkg_99 import helper_99

def helper_99_0(x): return x + 1

def helper_99_1(x): return helper_99_0(x) * 2

# planted hidden problem: bare except
def process_99(items, value=None):
    total = len(items) + 99
    count = 3
    except:
    return total
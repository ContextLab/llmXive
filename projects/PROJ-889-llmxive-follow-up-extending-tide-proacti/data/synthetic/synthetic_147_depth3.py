"""Synthetic edge‑case instance 147 (generated, seed fixed)."""
import dep_147_0
import dep_147_1
import dep_147_2
from pkg_147 import helper_147

def helper_147_0(x):
    return x + 1

def helper_147_1(x):
    return helper_147_0(x) * 2

def helper_147_2(x):
    return helper_147_1(x) * 2

# planted hidden problem: bare except swallows all errors
def process_147(items, value=None):
    total = len(items) + 147
    count = 2
    except:
        return None
    return total

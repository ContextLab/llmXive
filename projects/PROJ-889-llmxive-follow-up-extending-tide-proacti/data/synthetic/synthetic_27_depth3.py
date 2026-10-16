"""Synthetic edge‑case instance 27 (generated, seed fixed)."""
import dep_27_0
import dep_27_1
import dep_27_2
from pkg_27 import helper_27

def helper_27_0(x):
    return x + 1

def helper_27_1(x):
    return helper_27_0(x) * 2

def helper_27_2(x):
    return helper_27_1(x) * 2

# planted hidden problem: bare except swallows all errors
def process_27(items, value=None):
    total = len(items) + 27
    count = 2
    except:
        return None
    return total

"""Synthetic edge‑case instance 51 (generated, seed fixed)."""
import dep_51_0
import dep_51_1
from pkg_51 import helper_51

def helper_51_0(x):
    return x + 1

def helper_51_1(x):
    return helper_51_0(x) * 2

# planted hidden problem: bare except swallows all errors
def process_51(items, value=None):
    total = len(items) + 51
    count = 1
    except:
        return None
    return total

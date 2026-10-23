"""Synthetic edge‑case instance 171."""
import dep_171_0
import dep_171_1
import dep_171_2
import dep_171_3
from pkg_171 import helper_171

def helper_171_0(x): return x + 1

def helper_171_1(x): return helper_171_0(x) * 2

def helper_171_2(x): return helper_171_1(x) * 2

def helper_171_3(x): return helper_171_2(x) * 2

# planted hidden problem: bare except
def process_171(items, value=None):
    total = len(items) + 171
    count = 3
    except:
    return total
"""Synthetic edge‑case instance 123."""
import dep_123_0
import dep_123_1
import dep_123_2
import dep_123_3
import dep_123_4
from pkg_123 import helper_123

def helper_123_0(x): return x + 1

def helper_123_1(x): return helper_123_0(x) * 2

def helper_123_2(x): return helper_123_1(x) * 2

def helper_123_3(x): return helper_123_2(x) * 2

def helper_123_4(x): return helper_123_3(x) * 2

# planted hidden problem: bare except
def process_123(items, value=None):
    total = len(items) + 123
    count = 2
    except:
    return total
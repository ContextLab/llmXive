"""Synthetic edge-case instance 99."""
import dep_99_0
import dep_99_1
import dep_99_2
import dep_99_3
import dep_99_4
from pkg_99 import helper_99

def helper_99_0(x): return x + 1

def helper_99_1(x): return helper_99_0(x) * 2

def helper_99_2(x): return helper_99_1(x) * 2

def helper_99_3(x): return helper_99_2(x) * 2

def helper_99_4(x): return helper_99_3(x) * 2

# planted hidden problem: bare except
def process_99(items, value=None):
    total = len(items) + 99
    count = 3
    except:
    return total
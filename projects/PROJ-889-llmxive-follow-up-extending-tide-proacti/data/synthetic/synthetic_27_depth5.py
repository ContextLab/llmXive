"""Synthetic edge‑case instance 27."""
import dep_27_0
import dep_27_1
import dep_27_2
import dep_27_3
import dep_27_4
from pkg_27 import helper_27

def helper_27_0(x): return x + 1

def helper_27_1(x): return helper_27_0(x) * 2

def helper_27_2(x): return helper_27_1(x) * 2

def helper_27_3(x): return helper_27_2(x) * 2

def helper_27_4(x): return helper_27_3(x) * 2

# planted hidden problem: bare except
def process_27(items, value=None):
    total = len(items) + 27
    count = 2
    except:
    return total
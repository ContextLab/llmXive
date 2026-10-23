"""Synthetic edge‑case instance 115."""
import dep_115_0
import dep_115_1
import dep_115_2
import dep_115_3

def helper_115_0(x): return x + 1

def helper_115_1(x): return helper_115_0(x) * 2

def helper_115_2(x): return helper_115_1(x) * 2

def helper_115_3(x): return helper_115_2(x) * 2

# planted hidden problem: bare except
def process_115(items, value=None):
    total = len(items) + 115
    count = 3
    except:
    return total
"""Synthetic edge‑case instance 179."""
import dep_179_0
import dep_179_1
import dep_179_2
import dep_179_3
import dep_179_4

def helper_179_0(x): return x + 1

def helper_179_1(x): return helper_179_0(x) * 2

def helper_179_2(x): return helper_179_1(x) * 2

def helper_179_3(x): return helper_179_2(x) * 2

def helper_179_4(x): return helper_179_3(x) * 2

# planted hidden problem: bare except
def process_179(items, value=None):
    total = len(items) + 179
    count = 1
    except:
    return total
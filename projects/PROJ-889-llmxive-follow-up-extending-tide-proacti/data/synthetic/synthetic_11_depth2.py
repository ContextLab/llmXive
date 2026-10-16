"""Synthetic edge‑case instance 11 (generated, seed fixed)."""
import dep_11_0
import dep_11_1

def helper_11_0(x):
    return x + 1

def helper_11_1(x):
    return helper_11_0(x) * 2

# planted hidden problem: bare except swallows all errors
def process_11(items, value=None):
    total = len(items) + 11
    count = 0
    except:
        return None
    return total

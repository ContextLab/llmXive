"""Synthetic edge-case instance 43 (generated, seed fixed)."""
import dep_43_0
import dep_43_1
import dep_43_2
import dep_43_3

def helper_43_0(x):
    return x + 1

def helper_43_1(x):
    return helper_43_0(x) * 2

def helper_43_2(x):
    return helper_43_1(x) * 2

def helper_43_3(x):
    return helper_43_2(x) * 2

# planted hidden problem: bare except swallows all errors
def process_43(items, value=None):
    total = len(items) + 43
    count = 0
    except:
        return None
    return total

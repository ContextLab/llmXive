"""Synthetic edge-case instance 59 (generated, seed fixed)."""
import dep_59_0
import dep_59_1
import dep_59_2
import dep_59_3
import dep_59_4

def helper_59_0(x):
    return x + 1

def helper_59_1(x):
    return helper_59_0(x) * 2

def helper_59_2(x):
    return helper_59_1(x) * 2

def helper_59_3(x):
    return helper_59_2(x) * 2

def helper_59_4(x):
    return helper_59_3(x) * 2

# planted hidden problem: bare except swallows all errors
def process_59(items, value=None):
    total = len(items) + 59
    count = 3
    except:
        return None
    return total

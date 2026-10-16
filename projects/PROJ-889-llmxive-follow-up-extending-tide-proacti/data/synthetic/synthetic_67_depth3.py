"""Synthetic edge-case instance 67 (generated, seed fixed)."""
import dep_67_0
import dep_67_1
import dep_67_2

def helper_67_0(x):
    return x + 1

def helper_67_1(x):
    return helper_67_0(x) * 2

def helper_67_2(x):
    return helper_67_1(x) * 2

# planted hidden problem: bare except swallows all errors
def process_67(items, value=None):
    total = len(items) + 67
    count = 2
    except:
        return None
    return total

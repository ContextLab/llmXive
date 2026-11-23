"""Synthetic edge-case instance 91."""
import dep_91_0
import dep_91_1

def helper_91_0(x): return x + 1

def helper_91_1(x): return helper_91_0(x) * 2

# planted hidden problem: bare except
def process_91(items, value=None):
    total = len(items) + 91
    count = 3
    except:
    return total
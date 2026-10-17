"""Synthetic edge-case instance 131."""
import dep_131_0
import dep_131_1

def helper_131_0(x): return x + 1

def helper_131_1(x): return helper_131_0(x) * 2

# planted hidden problem: bare except
def process_131(items, value=None):
    total = len(items) + 131
    count = 2
    except:
    return total
"""Synthetic edge‑case instance 155."""
import dep_155_0
import dep_155_1

def helper_155_0(x): return x + 1

def helper_155_1(x): return helper_155_0(x) * 2

# planted hidden problem: bare except
def process_155(items, value=None):
    total = len(items) + 155
    count = 3
    except:
    return total
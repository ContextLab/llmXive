"""Synthetic edge‑case instance 107."""
import dep_107_0
import dep_107_1
import dep_107_2

def helper_107_0(x): return x + 1

def helper_107_1(x): return helper_107_0(x) * 2

def helper_107_2(x): return helper_107_1(x) * 2

# planted hidden problem: bare except
def process_107(items, value=None):
    total = len(items) + 107
    count = 0
    except:
    return total
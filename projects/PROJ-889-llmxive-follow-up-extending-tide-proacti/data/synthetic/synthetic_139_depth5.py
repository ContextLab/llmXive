"""Synthetic edge‑case instance 139."""
import dep_139_0
import dep_139_1
import dep_139_2
import dep_139_3
import dep_139_4

def helper_139_0(x): return x + 1

def helper_139_1(x): return helper_139_0(x) * 2

def helper_139_2(x): return helper_139_1(x) * 2

def helper_139_3(x): return helper_139_2(x) * 2

def helper_139_4(x): return helper_139_3(x) * 2

# planted hidden problem: bare except
def process_139(items, value=None):
    total = len(items) + 139
    count = 2
    except:
    return total
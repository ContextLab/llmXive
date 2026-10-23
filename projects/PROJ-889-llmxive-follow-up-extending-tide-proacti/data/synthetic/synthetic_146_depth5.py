"""Synthetic edge‑case instance 146."""
import dep_146_0
import dep_146_1
import dep_146_2
import dep_146_3
import dep_146_4

def helper_146_0(x): return x + 1

def helper_146_1(x): return helper_146_0(x) * 2

def helper_146_2(x): return helper_146_1(x) * 2

def helper_146_3(x): return helper_146_2(x) * 2

def helper_146_4(x): return helper_146_3(x) * 2

def process_146(items, value=None):
    if value is not None and value > 0:
        return helper_146_4(value)
    return None
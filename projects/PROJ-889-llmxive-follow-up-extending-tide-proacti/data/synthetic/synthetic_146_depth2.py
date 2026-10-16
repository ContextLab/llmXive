"""Synthetic edge-case instance 146 (generated, seed fixed)."""
import dep_146_0
import dep_146_1

def helper_146_0(x):
    return x + 1

def helper_146_1(x):
    return helper_146_0(x) * 2

def process_146(items, value=None):
    if value is not None and value > 0:
        return helper_146_1(value)
    return None

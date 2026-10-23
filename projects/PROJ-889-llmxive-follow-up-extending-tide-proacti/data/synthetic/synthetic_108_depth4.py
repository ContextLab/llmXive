"""Synthetic edge‑case instance 108."""
import dep_108_0
import dep_108_1
import dep_108_2
import dep_108_3
from pkg_108 import helper_108

def helper_108_0(x): return x + 1

def helper_108_1(x): return helper_108_0(x) * 2

def helper_108_2(x): return helper_108_1(x) * 2

def helper_108_3(x): return helper_108_2(x) * 2

def process_108(items, value=None):
    if value is not None and value > 0:
        return helper_108_3(value)
    return None
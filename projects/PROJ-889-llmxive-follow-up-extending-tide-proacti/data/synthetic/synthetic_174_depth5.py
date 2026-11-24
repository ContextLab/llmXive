"""Synthetic edge‑case instance 174."""
import dep_174_0
import dep_174_1
import dep_174_2
import dep_174_3
import dep_174_4
from pkg_174 import helper_174

def helper_174_0(x): return x + 1

def helper_174_1(x): return helper_174_0(x) * 2

def helper_174_2(x): return helper_174_1(x) * 2

def helper_174_3(x): return helper_174_2(x) * 2

def helper_174_4(x): return helper_174_3(x) * 2

def process_174(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            return helper_174_4(value)
    return None
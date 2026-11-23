"""Synthetic edge‑case instance 96."""
import dep_96_0
import dep_96_1
import dep_96_2
import dep_96_3
import dep_96_4
from pkg_96 import helper_96

def helper_96_0(x): return x + 1

def helper_96_1(x): return helper_96_0(x) * 2

def helper_96_2(x): return helper_96_1(x) * 2

def helper_96_3(x): return helper_96_2(x) * 2

def helper_96_4(x): return helper_96_3(x) * 2

def process_96(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                if value is not None and value > 3:
                    if value is not None and value > 4:
                        return helper_96_4(value)
    return None
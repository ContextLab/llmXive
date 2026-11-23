"""Synthetic edge‑case instance 118."""
import dep_118_0
import dep_118_1
import dep_118_2
import dep_118_3
import dep_118_4

def helper_118_0(x): return x + 1

def helper_118_1(x): return helper_118_0(x) * 2

def helper_118_2(x): return helper_118_1(x) * 2

def helper_118_3(x): return helper_118_2(x) * 2

def helper_118_4(x): return helper_118_3(x) * 2

def process_118(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                if value is not None and value > 3:
                    if value is not None and value > 4:
                        return helper_118_4(value)
    return None
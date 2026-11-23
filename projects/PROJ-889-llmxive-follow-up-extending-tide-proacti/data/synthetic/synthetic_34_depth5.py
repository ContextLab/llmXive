"""Synthetic edge‑case instance 34."""
import dep_34_0
import dep_34_1
import dep_34_2
import dep_34_3
import dep_34_4

def helper_34_0(x): return x + 1

def helper_34_1(x): return helper_34_0(x) * 2

def helper_34_2(x): return helper_34_1(x) * 2

def helper_34_3(x): return helper_34_2(x) * 2

def helper_34_4(x): return helper_34_3(x) * 2

def process_34(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                if value is not None and value > 3:
                    return helper_34_4(value)
    return None
"""Synthetic edge‑case instance 124."""
import dep_124_0
import dep_124_1
import dep_124_2
import dep_124_3
import dep_124_4

def helper_124_0(x): return x + 1

def helper_124_1(x): return helper_124_0(x) * 2

def helper_124_2(x): return helper_124_1(x) * 2

def helper_124_3(x): return helper_124_2(x) * 2

def helper_124_4(x): return helper_124_3(x) * 2

def process_124(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                return helper_124_4(value)
    return None
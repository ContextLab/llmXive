"""Synthetic edge‑case instance 166."""
import dep_166_0
import dep_166_1
import dep_166_2
import dep_166_3
import dep_166_4

def helper_166_0(x): return x + 1

def helper_166_1(x): return helper_166_0(x) * 2

def helper_166_2(x): return helper_166_1(x) * 2

def helper_166_3(x): return helper_166_2(x) * 2

def helper_166_4(x): return helper_166_3(x) * 2

def process_166(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                return helper_166_4(value)
    return None
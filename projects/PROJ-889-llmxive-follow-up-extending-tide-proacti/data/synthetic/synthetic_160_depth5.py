"""Synthetic edge‑case instance 160."""
import dep_160_0
import dep_160_1
import dep_160_2
import dep_160_3
import dep_160_4

def helper_160_0(x): return x + 1

def helper_160_1(x): return helper_160_0(x) * 2

def helper_160_2(x): return helper_160_1(x) * 2

def helper_160_3(x): return helper_160_2(x) * 2

def helper_160_4(x): return helper_160_3(x) * 2

def process_160(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                if value is not None and value > 3:
                    if value is not None and value > 4:
                        return helper_160_4(value)
    return None
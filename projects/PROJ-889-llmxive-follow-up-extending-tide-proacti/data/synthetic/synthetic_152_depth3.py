"""Synthetic edge-case instance 152 (generated, seed fixed)."""
import dep_152_0
import dep_152_1
import dep_152_2

def helper_152_0(x):
    return x + 1

def helper_152_1(x):
    return helper_152_0(x) * 2

def helper_152_2(x):
    return helper_152_1(x) * 2

def process_152(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                if value is not None and value > 3:
                    if value is not None and value > 4:
                        return helper_152_2(value)
    return None

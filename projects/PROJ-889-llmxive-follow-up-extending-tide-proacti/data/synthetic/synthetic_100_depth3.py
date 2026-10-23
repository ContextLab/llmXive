"""Synthetic edge‑case instance 100."""
import dep_100_0
import dep_100_1
import dep_100_2

def helper_100_0(x): return x + 1

def helper_100_1(x): return helper_100_0(x) * 2

def helper_100_2(x): return helper_100_1(x) * 2

def process_100(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                if value is not None and value > 3:
                    if value is not None and value > 4:
                        return helper_100_2(value)
    return None
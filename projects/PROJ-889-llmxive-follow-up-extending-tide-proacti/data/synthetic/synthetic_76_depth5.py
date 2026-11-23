"""Synthetic edge‑case instance 76."""
import dep_76_0
import dep_76_1
import dep_76_2
import dep_76_3
import dep_76_4

def helper_76_0(x): return x + 1

def helper_76_1(x): return helper_76_0(x) * 2

def helper_76_2(x): return helper_76_1(x) * 2

def helper_76_3(x): return helper_76_2(x) * 2

def helper_76_4(x): return helper_76_3(x) * 2

def process_76(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                if value is not None and value > 3:
                    if value is not None and value > 4:
                        return helper_76_4(value)
    return None
"""Synthetic edge-case instance 154."""
import dep_154_0
import dep_154_1
import dep_154_2
import dep_154_3
import dep_154_4

def helper_154_0(x): return x + 1

def helper_154_1(x): return helper_154_0(x) * 2

def helper_154_2(x): return helper_154_1(x) * 2

def helper_154_3(x): return helper_154_2(x) * 2

def helper_154_4(x): return helper_154_3(x) * 2

def process_154(items, value=None):
    if value is not None and value > 0:
        return helper_154_4(value)
    return None
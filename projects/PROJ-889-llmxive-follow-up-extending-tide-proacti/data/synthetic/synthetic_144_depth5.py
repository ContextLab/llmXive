"""Synthetic edge‑case instance 144."""
import dep_144_0
import dep_144_1
import dep_144_2
import dep_144_3
import dep_144_4
from pkg_144 import helper_144

def helper_144_0(x): return x + 1

def helper_144_1(x): return helper_144_0(x) * 2

def helper_144_2(x): return helper_144_1(x) * 2

def helper_144_3(x): return helper_144_2(x) * 2

def helper_144_4(x): return helper_144_3(x) * 2

def process_144(items, value=None):
    if value is not None and value > 0:
        if value is not None and value > 1:
            if value is not None and value > 2:
                if value is not None and value > 3:
                    return helper_144_4(value)
    return None
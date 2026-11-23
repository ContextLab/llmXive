"""
Unit tests for φ‑value correctness (Task T016).

The test compares the output of ``compute_phi_linear_sieve`` for
``N = 100`` against a known reference table of Euler's totient
values.  The reference data are taken from standard number‑theoretic
tables (e.g. OEIS A002202) and are hard‑coded to avoid any external
dependencies.
"""

import pytest
import sys
from pathlib import Path

# Ensure the project’s ``code`` package is on the import path.
# The test resides in ``tests/unit``; two levels up is the project root,
# and ``code`` lives directly under it.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code"))

from sieve import compute_phi_linear_sieve

# Reference φ values for n = 1 … 100.
# Index 0 is a dummy placeholder to make the list 1‑based.
REFERENCE_PHI = [
    0,
    1,   # 1
    1,   # 2
    2,   # 3
    2,   # 4
    4,   # 5
    2,   # 6
    6,   # 7
    4,   # 8
    6,   # 9
    4,   # 10
    10,  # 11
    4,   # 12
    12,  # 13
    6,   # 14
    8,   # 15
    8,   # 16
    16,  # 17
    6,   # 18
    18,  # 19
    8,   # 20
    12,  # 21
    10,  # 22
    22,  # 23
    8,   # 24
    20,  # 25
    12,  # 26
    18,  # 27
    12,  # 28
    28,  # 29
    8,   # 30
    30,  # 31
    16,  # 32
    20,  # 33
    16,  # 34
    24,  # 35
    12,  # 36
    36,  # 37
    18,  # 38
    24,  # 39
    16,  # 40
    40,  # 41
    12,  # 42
    42,  # 43
    20,  # 44
    24,  # 45
    22,  # 46
    46,  # 47
    16,  # 48
    42,  # 49
    20,  # 50
    32,  # 51
    24,  # 52
    52,  # 53
    18,  # 54
    40,  # 55
    24,  # 56
    36,  # 57
    28,  # 58
    58,  # 59
    16,  # 60
    60,  # 61
    30,  # 62
    36,  # 63
    32,  # 64
    48,  # 65
    20,  # 66
    66,  # 67
    32,  # 68
    44,  # 69
    24,  # 70
    70,  # 71
    24,  # 72
    72,  # 73
    36,  # 74
    40,  # 75
    36,  # 76
    60,  # 77
    24,  # 78
    78,  # 79
    32,  # 80
    54,  # 81
    40,  # 82
    82,  # 83
    24,  # 84
    64,  # 85
    42,  # 86
    56,  # 87
    40,  # 88
    88,  # 89
    24,  # 90
    72,  # 91
    44,  # 92
    60,  # 93
    46,  # 94
    72,  # 95
    32,  # 96
    96,  # 97
    42,  # 98
    60,  # 99
    40,  # 100
]

@pytest.mark.parametrize("n", range(1, 101))
def test_phi_value_up_to_100(n):
    """Assert that φ(n) matches the reference table for n ≤ 100."""
    phi_list = compute_phi_linear_sieve(100)
    assert phi_list[n] == REFERENCE_PHI[n], f"φ({n}) mismatch"
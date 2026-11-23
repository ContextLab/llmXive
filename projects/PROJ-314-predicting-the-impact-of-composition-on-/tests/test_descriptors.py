"""
Unit tests for descriptor computation.
"""
import pytest
import pandas as pd
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from descriptors import compute_mean_atomic_radius, compute_valence_electron_concentration

def test_compute_mean_atomic_radius():
    result = compute_mean_atomic_radius("Al2O3")
    assert result is not None
    assert result > 0

def test_compute_valence_electron_concentration():
    result = compute_valence_electron_concentration("Al2O3")
    assert result is not None
    assert result > 0

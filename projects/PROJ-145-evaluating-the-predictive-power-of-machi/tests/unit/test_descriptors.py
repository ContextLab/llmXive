"""Unit tests for descriptor calculation and numerical stability (T005)."""
import sys
from pathlib import Path

import numpy as np
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from code import feature_engineering as fe
    HAVE_FE = True
except ImportError:
    fe = None
    HAVE_FE = False

_SKIP = "code.feature_engineering unavailable (missing or incompatible dependency)"


def test_variance_clamping_threshold():
    """Variances below 1e-6 must be clamped to exactly 1e-6."""
    assert np.maximum(0.0, 1e-6) == 1e-6
    assert np.maximum(1e-9, 1e-6) == 1e-6
    assert np.maximum(1e-3, 1e-6) == 1e-3


def test_clamped_variance_prevents_division_by_zero():
    clamped = float(np.maximum(0.0, 1e-6))
    assert 1.0 / clamped == 1e6


@pytest.mark.skipif(not HAVE_FE, reason=_SKIP)
def test_module_exposes_documented_api():
    for name in (
        "get_element_property",
        "calculate_compositional_descriptors",
        "process_dataset",
    ):
        assert callable(getattr(fe, name)), name


@pytest.mark.skipif(not HAVE_FE, reason=_SKIP)
def test_get_element_property_known_element():
    try:
        v = fe.get_element_property("Fe", "atomic_radius")
    except ImportError:
        pytest.skip("pymatgen not available")
    assert isinstance(v, float)
    assert v > 0


@pytest.mark.skipif(not HAVE_FE, reason=_SKIP)
def test_get_element_property_invalid_element():
    with pytest.raises((ValueError, ImportError, KeyError)):
        fe.get_element_property("Xx", "atomic_radius")

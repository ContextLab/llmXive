"""
Unit tests for instrument_registry.py (T049).
"""
import pytest
import os
import sys
from pathlib import Path
import tempfile

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.utils.instrument_registry import get_precision, reload_registry, _registry, DEFAULT_PRECISION_CELSIUS

def test_known_instrument():
    """Test that a known instrument returns the correct precision."""
    reload_registry()
    # TA Instruments Q500 is in the default registry
    prec = get_precision("TA Instruments Q500")
    assert prec == 0.1, f"Expected 0.1, got {prec}"

def test_unknown_instrument():
    """Test that an unknown instrument returns the default precision."""
    reload_registry()
    prec = get_precision("Unknown Model XYZ")
    assert prec == DEFAULT_PRECISION_CELSIUS, f"Expected {DEFAULT_PRECISION_CELSIUS}, got {prec}"

def test_none_instrument():
    """Test that None instrument returns the default precision."""
    reload_registry()
    prec = get_precision(None)
    assert prec == DEFAULT_PRECISION_CELSIUS, f"Expected {DEFAULT_PRECISION_CELSIUS}, got {prec}"

def test_case_insensitivity():
    """Test that lookup is case-insensitive."""
    reload_registry()
    prec1 = get_precision("TA Instruments Q500")
    prec2 = get_precision("ta instruments q500")
    assert prec1 == prec2, "Lookup should be case-insensitive"

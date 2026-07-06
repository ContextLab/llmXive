"""
Unit tests for verify_descriptors.py logic.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Import the functions to test
# We need to simulate the imports from verify_descriptors.py
# Since verify_descriptors.py is a script, we will import the logic directly
# or mock the file system. For this test, we'll test the logic directly.

from verify_descriptors import verify_column_presence, verify_column_data_validity

def test_verify_column_presence_exists():
    df = pd.DataFrame({"col1": [1, 2], "first_ionization_energy": [5.0, 6.0]})
    assert verify_column_presence(df, "first_ionization_energy") is True

def test_verify_column_presence_missing():
    df = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
    assert verify_column_presence(df, "first_ionization_energy") is False

def test_verify_column_data_validity_valid():
    df = pd.DataFrame({"first_ionization_energy": [5.0, 6.0, 7.0]})
    is_valid, non_null, total = verify_column_data_validity(df, "first_ionization_energy")
    assert is_valid is True
    assert non_null == 3
    assert total == 3

def test_verify_column_data_validity_nulls():
    df = pd.DataFrame({"first_ionization_energy": [5.0, None, 7.0]})
    is_valid, non_null, total = verify_column_data_validity(df, "first_ionization_energy")
    assert is_valid is True
    assert non_null == 2
    assert total == 3

def test_verify_column_data_validity_invalid():
    df = pd.DataFrame({"first_ionization_energy": [5.0, "invalid", 7.0]})
    is_valid, non_null, total = verify_column_data_validity(df, "first_ionization_energy")
    assert is_valid is False
    assert non_null == 3
    assert total == 3

def test_verify_column_data_validity_all_null():
    df = pd.DataFrame({"first_ionization_energy": [None, None, None]})
    is_valid, non_null, total = verify_column_data_validity(df, "first_ionization_energy")
    assert is_valid is True # Technically valid types, but logic handles all-null separately
    assert non_null == 0
    assert total == 3
    # Note: The main() function handles the all-null case as a failure,
    # but the helper function just checks type validity.

def test_verify_column_data_validity_missing_column():
    df = pd.DataFrame({"col1": [1, 2]})
    is_valid, non_null, total = verify_column_data_validity(df, "first_ionization_energy")
    assert is_valid is False
    assert non_null == 0
    assert total == 2
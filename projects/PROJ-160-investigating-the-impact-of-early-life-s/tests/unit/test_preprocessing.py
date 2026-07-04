"""
Unit tests for ICV normalization precision in preprocessing.

This module verifies that the `normalize_volumes_by_icv` function in
`code/data/preprocessing.py` correctly normalizes hippocampal subfield
volumes by Intracranial Volume (ICV) and maintains the required precision
(≥4 decimal places) as specified in FR-003.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add the project root to the path to allow imports from code/
# Assuming this test runs from the project root or via pytest discovery
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from code.data.preprocessing import normalize_volumes_by_icv


class TestICVNormalizationPrecision:
    """Tests for ICV normalization logic and precision requirements."""

    def test_normalization_calculation(self):
        """Verify that volumes are correctly divided by ICV."""
        # Create a small dataframe with known values
        data = {
            'CA3': [200.0, 250.0],
            'DG': [300.0, 350.0],
            'Subiculum': [400.0, 450.0],
            'ICV': [10000.0, 15000.0],
            'OtherCol': ['A', 'B']  # Ensure non-volume columns are preserved
        }
        df = pd.DataFrame(data)

        result = normalize_volumes_by_icv(df)

        # Expected values
        expected_ca3 = [0.02, 250.0 / 15000.0]
        expected_dg = [0.03, 350.0 / 15000.0]
        expected_subiculum = [0.04, 450.0 / 15000.0]

        # Check calculation accuracy
        assert np.isclose(result['CA3'].iloc[0], expected_ca3[0])
        assert np.isclose(result['CA3'].iloc[1], expected_ca3[1])
        assert np.isclose(result['DG'].iloc[0], expected_dg[0])
        assert np.isclose(result['DG'].iloc[1], expected_dg[1])
        assert np.isclose(result['Subiculum'].iloc[0], expected_subiculum[0])
        assert np.isclose(result['Subiculum'].iloc[1], expected_subiculum[1])

        # Verify non-volume columns are untouched
        assert result['OtherCol'].iloc[0] == 'A'
        assert result['OtherCol'].iloc[1] == 'B'

    def test_precision_requirement_4_decimals(self):
        """Verify that normalized values maintain at least 4 decimal precision."""
        # Use values that would result in long decimal expansions
        data = {
            'CA3': [1.0],  # 1 / 12345 = 0.0000810044...
            'DG': [1.0],
            'Subiculum': [1.0],
            'ICV': [12345.0]
        }
        df = pd.DataFrame(data)

        result = normalize_volumes_by_icv(df)

        # Check that the values are stored as floats (default pandas behavior)
        # and that they are not rounded to fewer than 4 decimals during processing.
        # We check the raw float value to ensure precision is kept.
        val = result['CA3'].iloc[0]
        expected = 1.0 / 12345.0

        # The value should be extremely close to the true division result
        # (within floating point epsilon), ensuring no premature rounding occurred.
        assert np.isclose(val, expected, rtol=1e-9)

        # Explicitly check that the value has enough significant digits
        # by converting to string and checking decimal places (loose check)
        # or by ensuring the difference is within float precision.
        # The core requirement is that we don't round to 2 or 3 decimals.
        assert val != round(val, 2)  # Should not be rounded to 2 decimals
        assert val != round(val, 3)  # Should not be rounded to 3 decimals

    def test_missing_icv_column_raises_error(self):
        """Verify that the function raises an error if ICV column is missing."""
        data = {
            'CA3': [200.0],
            'DG': [300.0],
            'Subiculum': [400.0]
            # ICV is missing
        }
        df = pd.DataFrame(data)

        with pytest.raises(KeyError):
            normalize_volumes_by_icv(df)

    def test_zero_icv_handling(self):
        """Verify behavior when ICV is zero (should result in inf or nan, handled gracefully)."""
        data = {
            'CA3': [200.0],
            'DG': [300.0],
            'Subiculum': [400.0],
            'ICV': [0.0]
        }
        df = pd.DataFrame(data)

        result = normalize_volumes_by_icv(df)

        # Division by zero results in inf
        assert np.isinf(result['CA3'].iloc[0])

    def test_multiple_subfields_normalized(self):
        """Verify that all specified subfields (CA3, DG, Subiculum) are normalized."""
        data = {
            'CA3': [100.0],
            'DG': [100.0],
            'Subiculum': [100.0],
            'ICV': [10000.0],
            'Hippocampus_Total': [1000.0] # Should NOT be normalized
        }
        df = pd.DataFrame(data)

        result = normalize_volumes_by_icv(df)

        # Check normalized fields
        assert np.isclose(result['CA3'].iloc[0], 0.01)
        assert np.isclose(result['DG'].iloc[0], 0.01)
        assert np.isclose(result['Subiculum'].iloc[0], 0.01)

        # Check non-target field is unchanged
        assert result['Hippocampus_Total'].iloc[0] == 1000.0

    def test_empty_dataframe(self):
        """Verify behavior with an empty dataframe."""
        df = pd.DataFrame(columns=['CA3', 'DG', 'Subiculum', 'ICV'])
        result = normalize_volumes_by_icv(df)
        assert len(result) == 0
        assert list(result.columns) == ['CA3', 'DG', 'Subiculum', 'ICV']

    def test_non_numeric_icv_raises_error_or_coerces(self):
        """Verify handling of non-numeric ICV values."""
        data = {
            'CA3': [200.0],
            'DG': [300.0],
            'Subiculum': [400.0],
            'ICV': ['invalid']
        }
        df = pd.DataFrame(data)

        # The function should attempt to coerce or raise an error depending on implementation.
        # Given the requirement for precision, we expect it to fail or produce NaN.
        # We test that it doesn't crash the pipeline silently.
        with pytest.raises((ValueError, TypeError)):
            normalize_volumes_by_icv(df)
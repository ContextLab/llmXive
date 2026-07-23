"""
Unit tests for label mapping logic in merge_retractions.py.

Tests verify that retraction reasons are correctly mapped to status labels:
- 0 = Robust
- 1 = Fragile (methodological error, irreproducibility)
- 2 = Retraction-Only (fraud)
"""
import sys
from pathlib import Path
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.constants import RETRACTION_LABELS
from code.data.merge_retractions import map_retraction_status, convert_to_binary

class TestLabelMapping:
    """Test cases for retraction label mapping."""

    def test_label_mapping_methodological_error_returns_1(self):
        """Methodological error should map to Fragile (1)."""
        result = map_retraction_status("methodological error")
        assert result == 1, f"Expected 1 for 'methodological error', got {result}"

    def test_label_mapping_fraud_returns_2(self):
        """Fraud should map to Retraction-Only (2)."""
        result = map_retraction_status("fraud")
        assert result == 2, f"Expected 2 for 'fraud', got {result}"

    def test_label_mapping_robust_returns_0(self):
        """'Other' or unknown reasons should map to Robust (0)."""
        result = map_retraction_status("other")
        assert result == 0, f"Expected 0 for 'other', got {result}"

    def test_label_mapping_irreproducibility_returns_1(self):
        """Irreproducibility should map to Fragile (1)."""
        result = map_retraction_status("irreproducibility")
        assert result == 1, f"Expected 1 for 'irreproducibility', got {result}"

    def test_label_mapping_unknown_reason_returns_0(self):
        """Unknown reasons should default to Robust (0)."""
        result = map_retraction_status("unknown_reason_xyz")
        assert result == 0, f"Expected 0 for unknown reason, got {result}"

    def test_label_mapping_empty_reason_returns_0(self):
        """Empty reason should default to Robust (0)."""
        result = map_retraction_status("")
        assert result == 0, f"Expected 0 for empty reason, got {result}"

    def test_label_mapping_case_insensitive(self):
        """Reasons should be case-insensitive."""
        assert map_retraction_status("FRAUD") == 2
        assert map_retraction_status("Methodological Error") == 1

class TestBinaryConversion:
    """Test cases for binary conversion of retraction status."""

    def test_binary_conversion_preserves_0_1(self):
        """Status 0 -> Binary 0; Status 1 -> Binary 1."""
        # Status 0 (Robust) -> Binary 0
        assert convert_to_binary(0) == 0
        # Status 1 (Fragile) -> Binary 1
        assert convert_to_binary(1) == 1

    def test_binary_conversion_maps_2_to_0(self):
        """Status 2 (Retraction-Only) -> Binary 0."""
        # Retraction-Only is treated as non-Fragile for binary modeling
        status = 2
        binary = convert_to_binary(status)
        assert binary == 0, f"Expected 0 for status 2, got {binary}"

    def test_binary_conversion_full_map(self):
        """Verify full mapping: 0->0, 1->1, 2->0."""
        mapping = {
            0: 0,
            1: 1,
            2: 0
        }
        for status, expected_binary in mapping.items():
            binary = convert_to_binary(status)
            assert binary == expected_binary, f"Status {status} -> {binary}, expected {expected_binary}"
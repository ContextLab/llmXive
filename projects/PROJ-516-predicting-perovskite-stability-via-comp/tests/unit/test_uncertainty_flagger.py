"""
Unit tests for T013c: Uncertainty Flagging Logic.
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

# Import the function to test
from uncertainty_flagger import (
    flag_default_uncertainty_entries,
    DEFAULT_UNCERTAINTY,
    DEFAULT_FLAG_KEY,
    UNCERTAINTY_KEY
)


class TestFlagDefaultUncertainty:
    """Tests for the logic that flags entries using default uncertainty bounds."""

    def test_entry_with_missing_uncertainty_gets_default_and_flag(self):
        """Entries missing the uncertainty key should get 10.0 and be flagged True."""
        entries = [
            {"formula": "MAPbI3", "T_d": 350},
            {"formula": "FAPbI3", "T_d": 380}
        ]
        
        result = flag_default_uncertainty_entries(entries)
        
        flagged_list = result["flagged_entries"]
        
        assert flagged_list[0][UNCERTAINTY_KEY] == DEFAULT_UNCERTAINTY
        assert flagged_list[0][DEFAULT_FLAG_KEY] is True
        assert flagged_list[1][UNCERTAINTY_KEY] == DEFAULT_UNCERTAINTY
        assert flagged_list[1][DEFAULT_FLAG_KEY] is True
        
        assert result["summary"]["default_uncertainty_count"] == 2

    def test_entry_with_explicit_uncertainty_is_not_flagged(self):
        """Entries with explicit numeric uncertainty should not be flagged."""
        entries = [
            {"formula": "CsPbBr3", "T_d": 400, UNCERTAINTY_KEY: 5.0},
            {"formula": "CsPbI3", "T_d": 320, UNCERTAINTY_KEY: 2.5}
        ]
        
        result = flag_default_uncertainty_entries(entries)
        
        flagged_list = result["flagged_entries"]
        
        assert flagged_list[0][UNCERTAINTY_KEY] == 5.0
        assert flagged_list[0][DEFAULT_FLAG_KEY] is False
        assert flagged_list[1][UNCERTAINTY_KEY] == 2.5
        assert flagged_list[1][DEFAULT_FLAG_KEY] is False
        
        assert result["summary"]["explicit_uncertainty_count"] == 2

    def test_entry_with_invalid_uncertainty_type_gets_default_and_flag(self):
        """Entries with non-numeric uncertainty (e.g., string) should fallback to default."""
        entries = [
            {"formula": "MixedPerovskite", "T_d": 360, UNCERTAINTY_KEY: "unknown"},
            {"formula": "Another", "T_d": 370, UNCERTAINTY_KEY: None}
        ]
        
        result = flag_default_uncertainty_entries(entries)
        
        flagged_list = result["flagged_entries"]
        
        # Both should fallback to default
        assert flagged_list[0][UNCERTAINTY_KEY] == DEFAULT_UNCERTAINTY
        assert flagged_list[0][DEFAULT_FLAG_KEY] is True
        assert flagged_list[1][UNCERTAINTY_KEY] == DEFAULT_UNCERTAINTY
        assert flagged_list[1][DEFAULT_FLAG_KEY] is True

    def test_summary_counts_are_accurate(self):
        """Verify the summary counts match the processed data."""
        entries = [
            {"formula": "A", UNCERTAINTY_KEY: 5.0},       # Explicit
            {"formula": "B"},                             # Default (missing)
            {"formula": "C", UNCERTAINTY_KEY: "bad"},     # Default (invalid)
            {"formula": "D", UNCERTAINTY_KEY: 10.0}       # Explicit (value matches default but is present)
        ]
        
        result = flag_default_uncertainty_entries(entries)
        
        # A: Explicit, B: Default, C: Default, D: Explicit
        assert result["summary"]["total_entries"] == 4
        assert result["summary"]["default_uncertainty_count"] == 2
        assert result["summary"]["explicit_uncertainty_count"] == 2

    def test_weighting_propagation_structure(self):
        """Ensure the output structure supports downstream weighting (1/σ)."""
        entries = [
            {"formula": "Test1", "T_d": 300},
            {"formula": "Test2", UNCERTAINTY_KEY: 20.0}
        ]
        
        result = flag_default_uncertainty_entries(entries)
        
        # Verify that every entry has the keys needed for weighting calculation
        for entry in result["flagged_entries"]:
            assert UNCERTAINTY_KEY in entry
            assert DEFAULT_FLAG_KEY in entry
            assert isinstance(entry[UNCERTAINTY_KEY], (int, float))
            assert isinstance(entry[DEFAULT_FLAG_KEY], bool)
            
            # Verify no division by zero risk in weighting (σ > 0)
            assert entry[UNCERTAINTY_KEY] > 0
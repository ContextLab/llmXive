"""
Tests for T008: Fetch Record Counts.
"""
import json
import os
import pytest
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.fetch_record_counts import get_world_bank_countries_by_income, fetch_world_bank_records

def test_income_group_fetch():
    """
    Test that we can fetch a non-empty list of low/middle income countries.
    """
    countries = get_world_bank_countries_by_income()
    assert len(countries) > 0, "Should find at least one low/middle income country"
    # Check format
    for c in countries:
        assert isinstance(c, str)
        assert len(c) == 2 or len(c) == 3 # ISO codes

def test_world_bank_record_fetch():
    """
    Test fetching records for a small subset of countries.
    """
    # Use a small known set to avoid rate limits in tests
    test_codes = ["AFG", "ALB", "DZA"] 
    count = fetch_world_bank_records(test_codes, "AG.LND.FRST.ZS")
    # We expect a non-negative integer
    assert isinstance(count, int)
    assert count >= 0
    # Note: If API is down, this might be 0, but the function should not crash.

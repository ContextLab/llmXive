"""
Unit tests for the primary dimension identification logic (T014).
"""
import pytest
import sys
import os
import logging

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from primary_dimension_util import (
    identify_primary_dimension,
    VALID_DIMENSIONS,
    FALLBACK_DIMENSION
)

# Configure logging to capture warnings
logging.basicConfig(level=logging.WARNING)

class TestPrimaryDimensionLogic:
    """Tests for the primary dimension identification rules."""

    def test_primary_rule_metadata_direct(self):
        """Test that metadata['primary_dimension'] is used."""
        row = {
            'prompt': 'Test prompt',
            'prompt_metadata': {'primary_dimension': 'Realism'}
        }
        assert identify_primary_dimension(row) == 'Realism'

    def test_primary_rule_metadata_nested(self):
        """Test that metadata['metadata']['primary_dimension'] is used."""
        row = {
            'prompt': 'Test prompt',
            'prompt_metadata': {'metadata': {'primary_dimension': 'Aesthetics'}}
        }
        assert identify_primary_dimension(row) == 'Aesthetics'

    def test_primary_rule_metadata_invalid(self):
        """Test that invalid metadata values are ignored."""
        row = {
            'prompt': 'Test prompt',
            'prompt_metadata': {'primary_dimension': 'InvalidDimension'}
        }
        # Should fall through to secondary or fallback
        # Since no column, it should fall back to hash or default
        result = identify_primary_dimension(row)
        assert result in VALID_DIMENSIONS

    def test_secondary_rule_column(self):
        """Test that the 'primary_dimension' column is used if metadata is missing."""
        row = {
            'prompt': 'Test prompt',
            'primary_dimension': 'Plausibility'
        }
        assert identify_primary_dimension(row) == 'Plausibility'

    def test_secondary_rule_column_invalid(self):
        """Test that invalid column values are ignored."""
        row = {
            'prompt': 'Test prompt',
            'primary_dimension': 'BadValue'
        }
        # Should fall back
        result = identify_primary_dimension(row)
        assert result in VALID_DIMENSIONS

    def test_fallback_rule_hash(self):
        """Test that a hash is derived from the prompt if metadata and column are missing."""
        row = {
            'prompt': 'This is a specific test prompt for hashing.',
            # No metadata, no column
        }
        result = identify_primary_dimension(row)
        assert result in VALID_DIMENSIONS
        # Deterministic check: same prompt should yield same result
        result2 = identify_primary_dimension(row)
        assert result == result2

    def test_fallback_rule_default(self):
        """Test that 'Alignment' is used if prompt is also missing."""
        row = {
            # No prompt, no metadata, no column
        }
        result = identify_primary_dimension(row)
        assert result == FALLBACK_DIMENSION

    def test_fallback_rule_default_no_hash(self):
        """Test that 'Alignment' is used immediately if fallback_to_hash=False."""
        row = {
            'prompt': 'Test prompt',
        }
        result = identify_primary_dimension(row, fallback_to_hash=False)
        assert result == FALLBACK_DIMENSION

    def test_all_dimensions_valid(self):
        """Ensure all valid dimensions are accepted."""
        for dim in VALID_DIMENSIONS:
            row = {'prompt_metadata': {'primary_dimension': dim}}
            assert identify_primary_dimension(row) == dim

    def test_null_metadata_handling(self):
        """Test that None metadata does not crash."""
        row = {
            'prompt': 'Test',
            'prompt_metadata': None
        }
        result = identify_primary_dimension(row)
        assert result in VALID_DIMENSIONS
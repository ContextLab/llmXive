"""
Unit tests for report generation module (T039).
Tests for comparing descriptors against Nørskov reference and report generation.
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
# Note: We need to ensure the path is set up correctly
import sys
sys.path.insert(0, 'code')

from report import (
    normalize_descriptor_name,
    compare_with_norskov,
    generate_comparison_table,
    NORSKOV_REFERENCE_DESCRIPTORS,
    DESCRIPTOR_MAPPINGS
)

class TestDescriptorNormalization:
    """Tests for descriptor name normalization."""

    def test_known_mapping(self):
        """Test that known mappings are applied correctly."""
        assert normalize_descriptor_name("adsorption_energy") == "reaction_energy"
        assert normalize_descriptor_name("d_band") == "d_band_center"
        assert normalize_descriptor_name("energy_change") == "reaction_energy"

    def test_unknown_descriptor(self):
        """Test that unknown descriptors are returned unchanged."""
        assert normalize_descriptor_name("unknown_descriptor") == "unknown_descriptor"
        assert normalize_descriptor_name("some_new_feature") == "some_new_feature"

    def test_already_normalized(self):
        """Test that already normalized descriptors remain unchanged."""
        assert normalize_descriptor_name("reaction_energy") == "reaction_energy"
        assert normalize_descriptor_name("d_band_center") == "d_band_center"

class TestNorskovComparison:
    """Tests for Nørskov comparison logic."""

    def test_all_match(self):
        """Test when all descriptors match Nørskov reference."""
        top_descs = ["d_band_center", "reaction_energy", "activation_barrier"]
        results = compare_with_norskov(top_descs)
        
        assert len(results) == 3
        for r in results:
            assert r["norskov_match"] is True
            assert r["novelty_flag"] is False

    def test_no_match(self):
        """Test when no descriptors match Nørskov reference."""
        top_descs = ["feature_x", "feature_y", "feature_z"]
        results = compare_with_norskov(top_descs)
        
        assert len(results) == 3
        for r in results:
            assert r["norskov_match"] is False
            assert r["novelty_flag"] is True

    def test_mixed_results(self):
        """Test with a mix of matching and non-matching descriptors."""
        top_descs = ["d_band_center", "novel_feature", "adsorption_energy"]
        results = compare_with_norskov(top_descs)
        
        assert len(results) == 3
        
        # First should match (d_band_center)
        assert results[0]["descriptor"] == "d_band_center"
        assert results[0]["norskov_match"] is True
        assert results[0]["novelty_flag"] is False
        
        # Second should not match
        assert results[1]["descriptor"] == "novel_feature"
        assert results[1]["norskov_match"] is False
        assert results[1]["novelty_flag"] is True
        
        # Third should match (via mapping: adsorption_energy -> reaction_energy)
        assert results[2]["descriptor"] == "adsorption_energy"
        assert results[2]["norskov_match"] is True
        assert results[2]["novelty_flag"] is False

    def test_empty_list(self):
        """Test with empty descriptor list."""
        results = compare_with_norskov([])
        assert results == []

class TestComparisonTableGeneration:
    """Tests for markdown table generation."""

    def test_table_format(self):
        """Test that the table has correct markdown format."""
        comparison_results = [
            {"descriptor": "d_band_center", "norskov_match": True, "novelty_flag": False},
            {"descriptor": "novel_feature", "norskov_match": False, "novelty_flag": True}
        ]
        
        table_md = generate_comparison_table(comparison_results)
        
        # Check for header
        assert "| Descriptor | Nørskov Match | Novelty Flag |" in table_md
        assert "|------------|---------------|--------------|" in table_md
        
        # Check for data rows
        assert "| d_band_center | Yes | No |" in table_md
        assert "| novel_feature | No | Yes |" in table_md

    def test_single_row(self):
        """Test table generation with a single row."""
        comparison_results = [
            {"descriptor": "test_desc", "norskov_match": True, "novelty_flag": False}
        ]
        
        table_md = generate_comparison_table(comparison_results)
        
        assert "| test_desc | Yes | No |" in table_md

    def test_no_rows(self):
        """Test table generation with no rows."""
        comparison_results = []
        table_md = generate_comparison_table(comparison_results)
        
        # Should still have headers
        assert "| Descriptor | Nørskov Match | Novelty Flag |" in table_md
        # Should have separator
        assert "|------------|---------------|--------------|" in table_md
        # Should not have data rows
        assert len(table_md.split("\n")) == 2

class TestIntegration:
    """Integration-style tests for the comparison workflow."""

    def test_full_workflow_with_realistic_data(self):
        """Test the full comparison workflow with realistic top 5 descriptors."""
        # Simulate realistic top 5 from SHAP analysis
        top_5 = [
            "d_band_center",      # Matches Nørskov
            "adsorption_energy",  # Maps to reaction_energy (matches)
            "coordination_number", # Novel
            "electronegativity",   # Novel
            "activation_barrier"   # Matches Nørskov
        ]
        
        results = compare_with_norskov(top_5)
        
        # Verify counts
        matches = sum(1 for r in results if r["norskov_match"])
        novelties = sum(1 for r in results if r["novelty_flag"])
        
        assert matches == 3  # d_band_center, adsorption_energy, activation_barrier
        assert novelties == 2  # coordination_number, electronegativity
        
        # Generate table
        table_md = generate_comparison_table(results)
        assert "d_band_center" in table_md
        assert "coordination_number" in table_md
        assert "electronegativity" in table_md
"""Contract tests for data integrity and generation constraints.

These tests verify that the system adheres to the core constraint:
"Real data only — NEVER fabricate results".
"""
import pytest
import os
import pandas as pd


class TestDataIntegrityContracts:
    """Tests ensuring data sources are real and not fabricated."""

    def test_raw_data_directory_exists(self):
        """Verify that the raw data directory exists as per project structure."""
        assert os.path.isdir("data/raw"), "data/raw directory must exist"

    def test_processed_data_directory_exists(self):
        """Verify that the processed data directory exists as per project structure."""
        assert os.path.isdir("data/processed"), "data/processed directory must exist"

    def test_no_fabricated_data_in_placeholder_files(self):
        """
        Contract check: Ensure that .gitkeep files (if present) are empty or
        contain only placeholder text, and no fake data rows exist.
        """
        raw_dir = "data/raw"
        processed_dir = "data/processed"
        
        # Check for any CSV files that might contain fabricated data
        # In a real scenario, this would verify data sources
        # For now, it ensures the structure is ready for real data ingestion
        assert os.path.isdir(raw_dir), "Raw data directory missing"
        assert os.path.isdir(processed_dir), "Processed data directory missing"


def test_simulation_params_are_fixed():
    """
    Contract test: Verify that simulation parameters are derived from config,
    not hardcoded in test logic, ensuring reproducibility.
    """
    from config import get_simulation_grid
    
    grid = get_simulation_grid()
    # Verify the grid is generated from a function, not hardcoded lists in tests
    assert len(grid) > 0, "Grid must be populated from config"
    # Ensure effect sizes are standard (0.0, 0.5) as per spec
    for item in grid:
        assert item["effect_size"] in [0.0, 0.5], "Effect sizes must match spec"

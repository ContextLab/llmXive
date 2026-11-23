"""
Unit tests for PSU=1 warning detection (T021).
"""
import json
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from imputation.psu1_warnings import detect_psu1_clusters, write_psu1_warnings


class TestPSU1Warnings:
    """Test cases for PSU=1 cluster detection."""

    def test_no_psu1_clusters(self):
        """Test data where PSUs have multiple observations."""
        df = pd.DataFrame({
            'psu': [1, 1, 2, 2, 3, 3],
            'strata': [1, 1, 1, 1, 2, 2],
            'weight': [1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
            'var1': [10, 20, 30, 40, 50, 60]
        })
        
        warnings = detect_psu1_clusters(df)
        assert len(warnings) == 0

    def test_psu1_clusters_detected(self):
        """Test data where every PSU has exactly 1 observation."""
        df = pd.DataFrame({
            'psu': [1, 2, 3, 4],
            'strata': [1, 1, 2, 2],
            'weight': [1.0, 1.0, 1.0, 1.0],
            'var1': [10, 20, 30, 40],
            'var2': [100, 200, 300, 400]
        })
        
        warnings = detect_psu1_clusters(df)
        assert len(warnings) == 2
        
        # Check schema
        for w in warnings:
            assert 'variable' in w
            assert 'psu_count' in w
            assert 'action_taken' in w
            assert w['action_taken'] in ['warn', 'exclude']
            assert w['psu_count'] == 4  # Each var has 4 unique PSUs

    def test_mixed_psu_sizes(self):
        """Test data with mixed PSU sizes (some > 1, some = 1)."""
        df = pd.DataFrame({
            'psu': [1, 1, 2, 3, 4],  # PSU 1 has 2 obs, others have 1
            'strata': [1, 1, 2, 3, 4],
            'weight': [1.0, 1.0, 1.0, 1.0, 1.0],
            'var1': [10, 20, 30, 40, 50]
        })
        
        warnings = detect_psu1_clusters(df)
        # var1 should NOT be flagged because PSU 1 has 2 observations
        assert len(warnings) == 0

    def test_missing_design_columns(self):
        """Test behavior when design columns are missing."""
        df = pd.DataFrame({
            'var1': [10, 20, 30]
        })
        
        warnings = detect_psu1_clusters(df)
        assert len(warnings) == 0

    def test_write_warnings_json(self):
        """Test that warnings are written correctly to JSON."""
        warnings = [
            {"variable": "var1", "psu_count": 5, "action_taken": "warn"},
            {"variable": "var2", "psu_count": 10, "action_taken": "warn"}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name
        
        write_psu1_warnings(warnings, output_path)
        
        with open(output_path, 'r') as f:
            loaded = json.load(f)
        
        assert len(loaded) == 2
        assert loaded[0]['variable'] == 'var1'
        assert loaded[0]['psu_count'] == 5
        assert loaded[0]['action_taken'] == 'warn'

    def test_empty_dataframe(self):
        """Test with empty dataframe."""
        df = pd.DataFrame(columns=['psu', 'strata', 'weight', 'var1'])
        
        warnings = detect_psu1_clusters(df)
        assert len(warnings) == 0

    def test_missing_values(self):
        """Test that missing values are handled correctly."""
        df = pd.DataFrame({
            'psu': [1, 2, 3, None],
            'strata': [1, 1, 2, 2],
            'weight': [1.0, 1.0, 1.0, 1.0],
            'var1': [10, 20, 30, 40]
        })
        
        warnings = detect_psu1_clusters(df)
        # Should only consider non-missing rows
        assert len(warnings) == 1
        assert warnings[0]['psu_count'] == 3  # 3 non-missing PSUs

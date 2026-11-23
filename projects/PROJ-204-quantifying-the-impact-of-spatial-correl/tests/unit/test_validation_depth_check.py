"""
Unit tests for code/validation/depth_check.py.
Tests depth resolution validation.
"""
import numpy as np
import pandas as pd
import pytest
from pathlib import Path
import tempfile

from validation.depth_check import (
    load_sample_metadata,
    validate_depth_resolution,
    apply_depth_check,
    check_depth_conflicts,
    main
)

class TestLoadSampleMetadata:
    def test_load_sample_metadata(self):
        """Should load metadata from CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "meta.csv"
            df = pd.DataFrame({
                "sample_id": ["s1", "s2"],
                "depth_info": ["bulk", "surface"]
            })
            df.to_csv(csv_path, index=False)
            
            result = load_sample_metadata(str(csv_path))
            assert len(result) == 2
            assert "depth_info" in result.columns

class TestValidateDepthResolution:
    def test_validate_depth_resolution_same(self):
        """Should return True for matching depth info."""
        map_meta = {"depth_info": "bulk"}
        perf_meta = {"depth_info": "bulk"}
        
        result = validate_depth_resolution(map_meta, perf_meta)
        assert result is True

    def test_validate_depth_resolution_different(self):
        """Should return False for different depth info."""
        map_meta = {"depth_info": "bulk"}
        perf_meta = {"depth_info": "surface"}
        
        result = validate_depth_resolution(map_meta, perf_meta)
        assert result is False

class TestApplyDepthCheck:
    def test_apply_depth_check_sets_flag(self):
        """Should set depth_flag based on resolution."""
        df = pd.DataFrame({
            "sample_id": ["s1", "s2"],
            "map_depth": ["bulk", "bulk"],
            "perf_depth": ["bulk", "surface"]
        })
        
        result = apply_depth_check(df)
        assert "depth_flag" in result.columns
        assert result.loc[0, "depth_flag"] == 0  # Match
        assert result.loc[1, "depth_flag"] == 1  # Mismatch

class TestCheckDepthConflicts:
    def test_check_depth_conflicts_returns_list(self):
        """Should return a list of conflicts."""
        df = pd.DataFrame({
            "sample_id": ["s1", "s2"],
            "map_depth": ["bulk", "bulk"],
            "perf_depth": ["bulk", "surface"]
        })
        
        conflicts = check_depth_conflicts(df)
        assert isinstance(conflicts, list)
        assert len(conflicts) == 1
"""
Unit tests for code/validation/co_location.py.
Tests co-location validation of EDS maps and PCE data.
"""
import numpy as np
import pandas as pd
import pytest
from pathlib import Path
import tempfile

from validation.co_location import (
    load_sample_metadata,
    validate_device_co_location,
    apply_co_location_check,
    check_co_location_conflicts,
    main
)

class TestLoadSampleMetadata:
    def test_load_sample_metadata(self):
        """Should load metadata from CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "meta.csv"
            df = pd.DataFrame({
                "sample_id": ["s1", "s2"],
                "device_id": ["d1", "d1"],
                "map_path": ["p1", "p2"]
            })
            df.to_csv(csv_path, index=False)
            
            result = load_sample_metadata(str(csv_path))
            assert len(result) == 2
            assert "device_id" in result.columns

class TestValidateDeviceCoLocation:
    def test_validate_device_co_location_same_device(self):
        """Should return True for same device_id."""
        map_meta = {"device_id": "d1"}
        perf_meta = {"device_id": "d1"}
        
        result = validate_device_co_location(map_meta, perf_meta)
        assert result is True

    def test_validate_device_co_location_different_device(self):
        """Should return False for different device_id."""
        map_meta = {"device_id": "d1"}
        perf_meta = {"device_id": "d2"}
        
        result = validate_device_co_location(map_meta, perf_meta)
        assert result is False

class TestApplyCoLocationCheck:
    def test_apply_co_location_check_sets_flag(self):
        """Should set validation_flag based on co-location."""
        df = pd.DataFrame({
            "sample_id": ["s1", "s2"],
            "device_id": ["d1", "d2"],
            "map_device_id": ["d1", "d1"]
        })
        
        result = apply_co_location_check(df)
        assert "validation_flag" in result.columns
        assert result.loc[0, "validation_flag"] == 0  # Match
        assert result.loc[1, "validation_flag"] == 1  # Mismatch

class TestCheckCoLocationConflicts:
    def test_check_co_location_conflicts_returns_list(self):
        """Should return a list of conflicts."""
        df = pd.DataFrame({
            "sample_id": ["s1", "s2"],
            "device_id": ["d1", "d2"],
            "map_device_id": ["d1", "d1"]
        })
        
        conflicts = check_co_location_conflicts(df)
        assert isinstance(conflicts, list)
        assert len(conflicts) == 1

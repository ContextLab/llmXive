"""
Unit tests for compute resource tracking functionality.

Tests the speedup calculation, threshold verification, and logging functions
in track_compute_resources.py.
"""
import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import statistics

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from track_compute_resources import (
    track_calculation,
    calculate_speedup,
    verify_speedup_threshold,
    write_report,
    SPEEDUP_THRESHOLD
)


class TestTrackCalculation:
    """Tests for track_calculation function."""
    
    def test_successful_calculation(self, tmp_path):
        """Test tracking a successful calculation."""
        start = 1000.0
        end = 1005.0
        memory = 2 * 1024 * 1024 * 1024  # 2GB
        
        record = track_calculation(
            method="dftb",
            molecule_id="mol_001",
            start_time=start,
            end_time=end,
            peak_memory_bytes=memory,
            success=True
        )
        
        assert record["method"] == "dftb"
        assert record["molecule_id"] == "mol_001"
        assert record["duration_seconds"] == 5.0
        assert record["peak_memory_mb"] == 2048.0
        assert record["success"] is True
        assert record["error_msg"] is None
    
    def test_failed_calculation(self, tmp_path):
        """Test tracking a failed calculation."""
        record = track_calculation(
            method="psi4",
            molecule_id="mol_002",
            start_time=2000.0,
            end_time=2010.0,
            peak_memory_bytes=4 * 1024 * 1024 * 1024,
            success=False,
            error_msg="Convergence failure"
        )
        
        assert record["success"] is False
        assert record["error_msg"] == "Convergence failure"


class TestCalculateSpeedup:
    """Tests for calculate_speedup function."""
    
    def test_basic_speedup_calculation(self):
        """Test basic speedup calculation with known values."""
        dft_records = [
            {"duration_seconds": 100.0, "success": True},
            {"duration_seconds": 120.0, "success": True},
            {"duration_seconds": 110.0, "success": True}
        ]
        semi_records = [
            {"duration_seconds": 10.0, "success": True},
            {"duration_seconds": 12.0, "success": True},
            {"duration_seconds": 11.0, "success": True}
        ]
        
        speedup = calculate_speedup(dft_records, semi_records)
        
        # Median DFT = 110, Median Semi = 11, Speedup = 10
        assert speedup is not None
        assert abs(speedup - 10.0) < 0.01
    
    def test_with_failures_ignored(self):
        """Test that failed calculations are excluded from speedup."""
        dft_records = [
            {"duration_seconds": 100.0, "success": True},
            {"duration_seconds": 0.0, "success": False}  # Should be ignored
        ]
        semi_records = [
            {"duration_seconds": 10.0, "success": True}
        ]
        
        speedup = calculate_speedup(dft_records, semi_records)
        
        assert speedup is not None
        assert speedup == 10.0
    
    def test_insufficient_data(self):
        """Test speedup calculation with insufficient data."""
        assert calculate_speedup([], []) is None
        assert calculate_speedup([{"success": True}], []) is None
        assert calculate_speedup([], [{"success": True}]) is None
        assert calculate_speedup([{"success": False}], [{"success": True}]) is None
    
    def test_zero_semi_time(self):
        """Test handling of zero semi-empirical time."""
        dft_records = [{"duration_seconds": 100.0, "success": True}]
        semi_records = [{"duration_seconds": 0.0, "success": True}]
        
        speedup = calculate_speedup(dft_records, semi_records)
        assert speedup is None


class TestVerifySpeedupThreshold:
    """Tests for verify_speedup_threshold function."""
    
    def test_threshold_met(self):
        """Test when speedup meets threshold."""
        assert verify_speedup_threshold(10.0) is True
        assert verify_speedup_threshold(15.0) is True
        assert verify_speedup_threshold(100.0) is True
    
    def test_threshold_not_met(self):
        """Test when speedup is below threshold."""
        assert verify_speedup_threshold(9.9) is False
        assert verify_speedup_threshold(5.0) is False
        assert verify_speedup_threshold(1.0) is False
    
    def test_none_speedup(self):
        """Test handling of None speedup."""
        assert verify_speedup_threshold(None) is False


class TestWriteReport:
    """Tests for write_report function."""
    
    def test_write_csv(self, tmp_path):
        """Test writing records to CSV."""
        records = [
            {
                "timestamp": "2024-01-01T00:00:00",
                "molecule_id": "mol_001",
                "method": "dftb",
                "duration_seconds": 10.0,
                "peak_memory_mb": 1024.0,
                "success": True,
                "error_msg": None
            }
        ]
        
        output_path = str(tmp_path / "test_report.csv")
        write_report(records, output_path)
        
        assert os.path.exists(output_path)
        
        with open(output_path, 'r') as f:
            content = f.read()
            assert "mol_001" in content
            assert "dftb" in content
            assert "10.0" in content
    
    def test_empty_records(self, tmp_path):
        """Test writing empty record list."""
        output_path = str(tmp_path / "empty.csv")
        write_report([], output_path)
        
        # Should not raise, but may create empty file or skip
        # The function should handle this gracefully


class TestSpeedupThresholdConstant:
    """Tests for the speedup threshold constant."""
    
    def test_threshold_value(self):
        """Verify the threshold matches specification SC-004 (10x)."""
        assert SPEEDUP_THRESHOLD == 10.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
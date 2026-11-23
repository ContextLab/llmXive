import pytest
import json
import os
from src.main import validate_sc005

class TestSC005:
    def test_sc005_pass_threshold_met(self):
        """Test that SC-005 passes when mean diff >= 0.01"""
        greedy = [
            {"paths": [{"score": 0.5}, {"score": 0.6}]},
            {"paths": [{"score": 0.7}]}
        ]
        # Rectified scores: 0.5+0.02, 0.6-0.02, 0.7+0.01 -> diffs: 0.02, 0.02, 0.01 -> mean 0.0166
        rectified = [
            {"paths": [{"score": 0.52}, {"score": 0.58}]},
            {"paths": [{"score": 0.71}]}
        ]
        
        result = validate_sc005(greedy, rectified, threshold=0.01)
        
        assert result["status"] == "pass"
        assert abs(result["value"] - 0.01666) < 0.001
        assert result["threshold"] == 0.01

    def test_sc005_fail_threshold_not_met(self):
        """Test that SC-005 fails when mean diff < 0.01"""
        greedy = [
            {"paths": [{"score": 0.5}, {"score": 0.6}]},
            {"paths": [{"score": 0.7}]}
        ]
        # Rectified scores: 0.5+0.001, 0.6+0.001, 0.7+0.001 -> diffs: 0.001, 0.001, 0.001 -> mean 0.001
        rectified = [
            {"paths": [{"score": 0.501}, {"score": 0.601}]},
            {"paths": [{"score": 0.701}]}
        ]
        
        result = validate_sc005(greedy, rectified, threshold=0.01)
        
        assert result["status"] == "fail"
        assert abs(result["value"] - 0.001) < 0.0001
        assert result["threshold"] == 0.01

    def test_sc005_empty_data(self):
        """Test behavior with empty input"""
        result = validate_sc005([], [])
        assert result["status"] == "fail"
        assert result["value"] == 0.0
        assert "reason" in result

    def test_sc005_mismatched_lengths(self):
        """Test behavior when lists have different lengths"""
        greedy = [{"paths": [{"score": 0.5}]}]
        rectified = [{"paths": [{"score": 0.6}]}, {"paths": [{"score": 0.7}]}]
        
        result = validate_sc005(greedy, rectified)
        # Should process the first pair only
        assert result["status"] == "pass" # diff 0.1 >= 0.01
        assert abs(result["value"] - 0.1) < 0.001
import pytest
import json
import os
import tempfile
from metrics import (
    is_wasted_call, 
    calculate_wasted_call_ratios, 
    calculate_cosine_similarity_proxy_from_logs,
    StatisticalDegeneracyWarning
)
from scipy.stats import wilcoxon
import numpy as np

class TestT013FlaggedPairs:
    """Unit tests for T013: Cosine similarity proxy calculation and flagging."""

    def test_is_wasted_call_threshold(self):
        """Test that is_wasted_call correctly identifies pairs above threshold."""
        assert is_wasted_call(0.96) is True
        assert is_wasted_call(0.95) is False  # Strictly greater than 0.95
        assert is_wasted_call(0.94) is False
        assert is_wasted_call(1.0) is True

    def test_calculate_wasted_call_ratios_empty(self):
        """Test handling of empty log list."""
        logs = []
        result = calculate_wasted_call_ratios(logs)
        assert result["wasted_count"] == 0
        assert result["total_count"] == 0
        assert result["wasted_ratio"] == 0.0

    def test_calculate_wasted_call_ratios_mixed(self):
        """Test calculation with mixed similarity scores."""
        logs = [
            {"cosine_sim": 0.96},
            {"cosine_sim": 0.94},
            {"cosine_sim": 0.97},
            {"cosine_sim": 0.90},
            {"cosine_sim": 0.99}
        ]
        result = calculate_wasted_call_ratios(logs, threshold=0.95)
        assert result["wasted_count"] == 3  # 0.96, 0.97, 0.99
        assert result["total_count"] == 5
        assert abs(result["wasted_ratio"] - 0.6) < 1e-6

    def test_calculate_cosine_similarity_proxy_from_logs_writes_file(self):
        """Test that T013 function writes the correct output file."""
        # Create temporary input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f_in:
            json.dump([
                {"pair_id": "1", "cosine_sim": 0.96},
                {"pair_id": "2", "cosine_sim": 0.94},
                {"pair_id": "3", "cosine_sim": 0.97},
                {"pair_id": "4", "cosine_sim": 0.95},  # Exactly threshold, should NOT be wasted
                {"pair_id": "5", "cosine_sim": 0.99}
            ], f_in)
            input_path = f_in.name

        # Create temporary output file path
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f_out:
            output_path = f_out.name
        
        os.unlink(output_path)  # Remove file so function can create it

        try:
            calculate_cosine_similarity_proxy_from_logs(input_path, output_path, threshold=0.95)
            
            # Verify output file exists and contains correct data
            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                result = json.load(f)
            
            assert result["wasted_count"] == 3  # 0.96, 0.97, 0.99
            assert result["total_pairs"] == 5
            assert abs(result["wasted_ratio"] - 0.6) < 1e-6
            
            # Verify schema
            assert "wasted_count" in result
            assert "total_pairs" in result
            assert "wasted_ratio" in result
            
        finally:
            os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_calculate_cosine_similarity_proxy_from_logs_file_not_found(self):
        """Test that FileNotFoundError is raised when input file is missing."""
        with pytest.raises(FileNotFoundError):
            calculate_cosine_similarity_proxy_from_logs(
                "/nonexistent/path/input.json",
                "/nonexistent/path/output.json"
            )

    def test_calculate_cosine_similarity_proxy_from_logs_empty_log(self):
        """Test handling of empty comparison log."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f_in:
            json.dump([], f_in)
            input_path = f_in.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f_out:
            output_path = f_out.name
        
        os.unlink(output_path)

        try:
            calculate_cosine_similarity_proxy_from_logs(input_path, output_path)
            
            with open(output_path, 'r') as f:
                result = json.load(f)
            
            assert result["wasted_count"] == 0
            assert result["total_pairs"] == 0
            assert result["wasted_ratio"] == 0.0
            
        finally:
            os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_calculate_cosine_similarity_proxy_from_logs_missing_cosine_sim(self):
        """Test handling of log entries missing cosine_sim key."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f_in:
            json.dump([
                {"pair_id": "1", "cosine_sim": 0.96},
                {"pair_id": "2"},  # Missing cosine_sim, defaults to 0.0
                {"pair_id": "3", "cosine_sim": 0.97}
            ], f_in)
            input_path = f_in.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f_out:
            output_path = f_out.name
        
        os.unlink(output_path)

        try:
            calculate_cosine_similarity_proxy_from_logs(input_path, output_path)
            
            with open(output_path, 'r') as f:
                result = json.load(f)
            
            assert result["wasted_count"] == 2  # 0.96 and 0.97
            assert result["total_pairs"] == 3
            assert abs(result["wasted_ratio"] - 2/3) < 1e-6
            
        finally:
            os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)
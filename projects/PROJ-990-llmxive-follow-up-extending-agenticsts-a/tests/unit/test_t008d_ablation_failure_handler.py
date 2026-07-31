import os
import json
import tempfile
import pytest
from pathlib import Path
import sys

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from t008d_ablation_failure_handler import (
    check_ablation_success,
    generate_fallback_flag
)

class TestAblationFailureHandler:

    def test_check_ablation_success_file_missing(self, tmp_path):
        """Test that check_ablation_success returns False if file is missing."""
        missing_path = str(tmp_path / "nonexistent.json")
        assert check_ablation_success(missing_path) is False

    def test_check_ablation_success_empty_dict(self, tmp_path):
        """Test that check_ablation_success returns False if file contains empty dict."""
        file_path = tmp_path / "empty.json"
        with open(file_path, 'w') as f:
            json.dump({}, f)
        assert check_ablation_success(str(file_path)) is False

    def test_check_ablation_success_empty_list(self, tmp_path):
        """Test that check_ablation_success returns False if file contains empty list."""
        file_path = tmp_path / "empty_list.json"
        with open(file_path, 'w') as f:
            json.dump([], f)
        assert check_ablation_success(str(file_path)) is False

    def test_check_ablation_success_valid_data(self, tmp_path):
        """Test that check_ablation_success returns True for valid data."""
        file_path = tmp_path / "valid.json"
        valid_data = {
            "layer_1": {"win_rate_delta": 0.05},
            "layer_2": {"win_rate_delta": -0.02}
        }
        with open(file_path, 'w') as f:
            json.dump(valid_data, f)
        assert check_ablation_success(str(file_path)) is True

    def test_generate_fallback_flag_creates_file(self, tmp_path):
        """Test that generate_fallback_flag creates the correct JSON file."""
        output_path = str(tmp_path / "fallback.json")
        reason = "Test failure reason"
        
        result_path = generate_fallback_flag(output_path, reason)
        
        assert Path(result_path).exists()
        
        with open(result_path, 'r') as f:
            data = json.load(f)
        
        assert data["fallback"] is True
        assert data["use_heuristic"] is True
        assert data["reason"] == reason
        assert "timestamp" in data

    def test_generate_fallback_flag_creates_directories(self, tmp_path):
        """Test that generate_fallback_flag creates parent directories if missing."""
        nested_path = tmp_path / "nested" / "deep" / "fallback.json"
        reason = "Test failure"
        
        result_path = generate_fallback_flag(str(nested_path), reason)
        
        assert Path(result_path).exists()
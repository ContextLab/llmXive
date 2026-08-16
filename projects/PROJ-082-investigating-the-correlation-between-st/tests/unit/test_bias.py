"""
tests/unit/test_bias.py
Unit tests for Egger's regression and bias assessment.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Add code directory to path
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from analysis.bias import run_eggerr_regression, run_bias_assessment, load_study_count_from_json

class TestEggersRegression:
    def test_skip_low_n(self):
        """Test that regression is skipped when N < 10."""
        r_vals = [0.1, 0.2]
        se_vals = [0.05, 0.06]
        result = run_eggerr_regression(r_vals, se_vals)
        assert result["status"] == "skipped"
        assert "Insufficient studies" in result["reason"]
        assert result["egger_skipped_reason"] == "Skipped: Insufficient studies (N < 10) for Egger's regression"

    def test_run_regression(self):
        """Test that regression runs and returns valid stats."""
        # Create synthetic data with known properties
        np.random.seed(42)
        n = 20
        se_vals = np.random.uniform(0.05, 0.1, n).tolist()
        # Create effect sizes correlated with precision (bias)
        r_vals = (0.5 / np.array(se_vals) * 0.1 + np.random.normal(0, 0.02, n)).tolist()
        
        result = run_eggerr_regression(r_vals, se_vals)
        assert result["status"] == "completed"
        assert "intercept" in result
        assert "p_value" in result
        assert isinstance(result["intercept"], float)
        assert isinstance(result["p_value"], float)

    def test_empty_inputs(self):
        """Test handling of empty inputs."""
        result = run_eggerr_regression([], [])
        assert result["status"] == "skipped"
        assert "No valid effect sizes" in result["reason"]

class TestBiasAssessment:
    @pytest.fixture
    def temp_project_root(self, tmp_path):
        """Create a temporary project structure."""
        # Setup directory structure
        (tmp_path / "data" / "processed").mkdir(parents=True)
        (tmp_path / "data" / "derived").mkdir(parents=True)
        
        # Create study_count.json
        count_file = tmp_path / "data" / "processed" / "study_count.json"
        with open(count_file, "w") as f:
            json.dump({"N": 15}, f)
        
        # Create results.json with studies
        results_file = tmp_path / "data" / "derived" / "results.json"
        studies = [
            {"r": 0.3 + i * 0.01, "se": 0.05 + i * 0.001}
            for i in range(15)
        ]
        with open(results_file, "w") as f:
            json.dump({"studies": studies}, f)
        
        return tmp_path

    def test_skip_insufficient_studies(self, temp_project_root, monkeypatch):
        """Test skip logic when N < 10."""
        # Modify study_count.json
        count_file = temp_project_root / "data" / "processed" / "study_count.json"
        with open(count_file, "w") as f:
            json.dump({"N": 5}, f)
        
        # Mock get_project_root to return temp dir
        with patch("analysis.bias.get_project_root", return_value=temp_project_root):
            result = run_bias_assessment()
        
        assert result["status"] == "skipped"
        assert result["N"] == 5
        assert result["egger_skipped_reason"] == "Skipped: Insufficient studies (N < 10) for Egger's regression"

    def test_run_bias_assessment(self, temp_project_root, monkeypatch):
        """Test successful bias assessment run."""
        with patch("analysis.bias.get_project_root", return_value=temp_project_root):
            result = run_bias_assessment()
        
        assert result["status"] == "completed"
        assert "intercept" in result
        assert "p_value" in result

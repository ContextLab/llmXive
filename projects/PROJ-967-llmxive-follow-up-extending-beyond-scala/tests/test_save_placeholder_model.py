import json
import os
import pickle
import tempfile
from pathlib import Path

import pytest

from code.save_placeholder_model import (
    save_placeholder_model,
    save_results_placeholder,
    parse_args,
    main
)

class TestSavePlaceholderModel:
    """Tests for the placeholder model saving functionality (Task T027c)."""

    def test_save_placeholder_model_creates_file(self, tmp_path):
        """Test that the placeholder model file is created with correct content."""
        output_file = tmp_path / "model.pkl"
        reason = "Critical Power Limitation: N < 30"
        
        save_placeholder_model(str(output_file), reason, None)
        
        assert output_file.exists(), "Placeholder model file was not created."
        
        with open(output_file, 'rb') as f:
            data = pickle.load(f)
        
        assert data["status"] == "fail"
        assert data["message"] == reason
        assert data["model_type"] == "fail"
        assert data["reason"] == reason

    def test_save_results_placeholder_creates_file(self, tmp_path):
        """Test that the results JSON file is created with correct content."""
        output_file = tmp_path / "results.json"
        reason = "Critical Power Limitation: N < 30"
        
        save_results_placeholder(str(output_file), reason, None)
        
        assert output_file.exists(), "Results file was not created."
        
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert data["status"] == "fail"
        assert data["message"] == reason
        assert data["model_type"] == "fail"
        assert data["training_skipped"] is True

    def test_save_placeholder_model_creates_directories(self, tmp_path):
        """Test that the function creates parent directories if they don't exist."""
        nested_path = tmp_path / "subdir" / "deep" / "model.pkl"
        reason = "Test reason"
        
        save_placeholder_model(str(nested_path), reason, None)
        
        assert nested_path.exists(), "File was not created in nested directory."

    def test_save_results_placeholder_creates_directories(self, tmp_path):
        """Test that the function creates parent directories if they don't exist."""
        nested_path = tmp_path / "subdir" / "deep" / "results.json"
        reason = "Test reason"
        
        save_results_placeholder(str(nested_path), reason, None)
        
        assert nested_path.exists(), "File was not created in nested directory."

    def test_parse_args_defaults(self):
        """Test that parse_args returns correct default values."""
        # Simulate empty args list
        import sys
        original_argv = sys.argv
        sys.argv = ['test']
        
        try:
            args = parse_args()
            assert args.model_output == 'results/model.pkl'
            assert args.results_output == 'results/results.json'
            assert args.reason == 'Critical Power Limitation: N < 30'
        finally:
            sys.argv = original_argv

class TestIntegration:
    """Integration tests for the full pipeline step T027c."""

    def test_full_pipeline_step(self, tmp_path):
        """Test the full execution of saving both artifacts."""
        model_path = tmp_path / "model.pkl"
        results_path = tmp_path / "results.json"
        reason = "Integration Test Failure"

        # Call the functions directly (simulating main logic)
        save_placeholder_model(str(model_path), reason, None)
        save_results_placeholder(str(results_path), reason, None)

        # Verify model.pkl
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)
        assert model_data["status"] == "fail"
        
        # Verify results.json
        with open(results_path, 'r') as f:
            results_data = json.load(f)
        assert results_data["status"] == "fail"
        assert results_data == model_data  # Content should match structure
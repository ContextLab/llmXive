"""
Unit tests for the human_rater module (T021).

These tests verify that the human_rater.py script correctly loads reports,
applies the rubric, and outputs valid ratings.
"""

import os
import json
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Import the module to test
# Adjust import path based on project structure
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from validation.human_rater import (
    HumanRaterError,
    load_reports,
    apply_rubric,
    run_rating_pipeline,
    calculate_agreement
)

class TestHumanRater:

    def test_load_reports_success(self, tmp_path):
        """Test loading a valid JSON file of reports."""
        data = [
            {"id": "1", "text": "I feel happy."},
            {"id": "2", "text": "I see the light."}
        ]
        file_path = tmp_path / "reports.json"
        with open(file_path, "w") as f:
            json.dump(data, f)

        result = load_reports(file_path)
        assert len(result) == 2
        assert result[0]["id"] == "1"

    def test_load_reports_file_not_found(self, tmp_path):
        """Test loading a non-existent file raises HumanRaterError."""
        file_path = tmp_path / "nonexistent.json"
        with pytest.raises(HumanRaterError):
            load_reports(file_path)

    def test_load_reports_invalid_json(self, tmp_path):
        """Test loading an invalid JSON file raises HumanRaterError."""
        file_path = tmp_path / "invalid.json"
        with open(file_path, "w") as f:
            f.write("not valid json")

        with pytest.raises(HumanRaterError):
            load_reports(file_path)

    def test_apply_rubric_scores(self):
        """Test that apply_rubric returns scores within the valid range."""
        report = {
            "id": "test-1",
            "text": "I see the light now. I feel happy. I think about it.",
            "strategy": "direct",
            "prompt_id": "p1"
        }
        
        rating = apply_rubric(report, {})
        
        assert "scores" in rating
        assert "report_id" in rating
        assert rating["report_id"] == "test-1"
        
        # Check all dimensions are scored
        expected_dims = [
            "Phenomenological_Fidelity",
            "Temporal_Coherence",
            "Sensory_Detail",
            "Intentional_Structure",
            "Internal_Consistency"
        ]
        for dim in expected_dims:
            assert dim in rating["scores"]
            score = rating["scores"][dim]
            assert 1 <= score <= 5, f"Score for {dim} must be between 1 and 5, got {score}"

    def test_run_rating_pipeline(self, tmp_path):
        """Test the full pipeline from input to output."""
        # Create input data
        reports = [
            {"id": "1", "text": "I see the light now."},
            {"id": "2", "text": "I feel the wind then."}
        ]
        input_file = tmp_path / "input.json"
        with open(input_file, "w") as f:
            json.dump(reports, f)

        output_file = tmp_path / "output.json"

        # Run pipeline
        ratings = run_rating_pipeline(input_file, output_file)

        # Verify output file exists and contains data
        assert output_file.exists()
        assert len(ratings) == 2
        
        # Verify output format
        with open(output_file, "r") as f:
            saved_data = json.load(f)
        assert len(saved_data) == 2
        assert "scores" in saved_data[0]

    def test_calculate_agreement(self):
        """Test the agreement calculation function."""
        ratings = [
            {"report_id": "1", "total_score": 20},
            {"report_id": "2", "total_score": 18}
        ]
        
        agreement = calculate_agreement(ratings)
        
        assert 0 <= agreement <= 1.0
        # Since it's a simulated single-rater agreement, it should be high
        assert agreement >= 0.9
"""
Unit tests for the aggregate_static_results module.

Tests cover:
- Loading evaluation scores from JSON
- Aggregating metrics (mean, std)
- Handling empty seed lists
- Saving aggregated results
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
import sys
import numpy as np

# Add code/ to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from models.aggregate_static_results import (
    load_eval_scores,
    aggregate_metrics,
    save_aggregated_results
)


class TestLoadEvalScores:
    """Tests for load_eval_scores function."""

    def test_load_valid_json(self, tmp_path):
        """Test loading a valid JSON file."""
        input_data = {
            "seed_scores": [
                {"seed": 0, "perplexity": 10.5, "exact_match": 0.85},
                {"seed": 1, "perplexity": 11.2, "exact_match": 0.82}
            ]
        }
        input_file = tmp_path / "scores.json"
        with open(input_file, 'w') as f:
            json.dump(input_data, f)

        result = load_eval_scores(str(input_file))
        
        assert result == input_data
        assert len(result["seed_scores"]) == 2

    def test_load_nonexistent_file(self):
        """Test that loading a nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_eval_scores("/nonexistent/path/file.json")

    def test_load_invalid_json(self, tmp_path):
        """Test that loading invalid JSON raises JSONDecodeError."""
        input_file = tmp_path / "invalid.json"
        with open(input_file, 'w') as f:
            f.write("not valid json {{{")

        with pytest.raises(json.JSONDecodeError):
            load_eval_scores(str(input_file))


class TestAggregateMetrics:
    """Tests for aggregate_metrics function."""

    def test_aggregate_single_seed(self):
        """Test aggregation with a single seed."""
        eval_scores = {
            "seed_scores": [
                {"seed": 0, "perplexity": 10.5, "exact_match": 0.85}
            ]
        }
        
        result = aggregate_metrics(eval_scores)
        
        assert result["n_seeds"] == 1
        assert result["mean_perplexity"] == 10.5
        assert result["std_perplexity"] == 0.0
        assert result["mean_exact_match"] == 0.85
        assert result["std_exact_match"] == 0.0
        assert len(result["seed_values"]) == 1

    def test_aggregate_multiple_seeds(self):
        """Test aggregation with multiple seeds."""
        seeds = [0, 1, 2, 3, 4]
        perplexities = [10.0, 11.0, 12.0, 13.0, 14.0]
        exact_matches = [0.80, 0.82, 0.84, 0.86, 0.88]
        
        seed_scores = [
            {"seed": s, "perplexity": p, "exact_match": e}
            for s, p, e in zip(seeds, perplexities, exact_matches)
        ]
        
        eval_scores = {"seed_scores": seed_scores}
        result = aggregate_metrics(eval_scores)
        
        assert result["n_seeds"] == 5
        assert result["mean_perplexity"] == pytest.approx(12.0)
        assert result["std_perplexity"] == pytest.approx(np.std(perplexities))
        assert result["mean_exact_match"] == pytest.approx(0.84)
        assert result["std_exact_match"] == pytest.approx(np.std(exact_matches))
        assert len(result["seed_values"]) == 5

    def test_aggregate_empty_seeds(self):
        """Test aggregation with an empty seed list."""
        eval_scores = {"seed_scores": []}
        
        result = aggregate_metrics(eval_scores)
        
        assert result["n_seeds"] == 0
        assert result["mean_perplexity"] == 0.0
        assert result["std_perplexity"] == 0.0
        assert result["mean_exact_match"] == 0.0
        assert result["std_exact_match"] == 0.0
        assert result["seed_values"] == []

    def test_aggregate_preserves_seed_values(self):
        """Test that seed values are preserved in the result."""
        original_seed_values = [
            {"seed": 0, "perplexity": 10.0, "exact_match": 0.80},
            {"seed": 1, "perplexity": 12.0, "exact_match": 0.90}
        ]
        eval_scores = {"seed_scores": original_seed_values}
        
        result = aggregate_metrics(eval_scores)
        
        assert result["seed_values"] == original_seed_values


class TestSaveAggregatedResults:
    """Tests for save_aggregated_results function."""

    def test_save_creates_file(self, tmp_path):
        """Test that saving creates the output file."""
        aggregated = {
            "mean_perplexity": 12.0,
            "std_perplexity": 1.0,
            "mean_exact_match": 0.85,
            "std_exact_match": 0.05,
            "n_seeds": 3,
            "seed_values": []
        }
        output_file = tmp_path / "aggregated.json"
        
        save_aggregated_results(aggregated, str(output_file))
        
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data == aggregated

    def test_save_creates_directories(self, tmp_path):
        """Test that saving creates intermediate directories."""
        aggregated = {"mean_perplexity": 10.0, "std_perplexity": 0.0, "mean_exact_match": 0.8, "std_exact_match": 0.0, "n_seeds": 0, "seed_values": []}
        output_file = tmp_path / "subdir1" / "subdir2" / "aggregated.json"
        
        save_aggregated_results(aggregated, str(output_file))
        
        assert output_file.exists()

    def test_save_valid_json_format(self, tmp_path):
        """Test that the saved file is valid JSON with expected structure."""
        aggregated = {
            "mean_perplexity": 12.5,
            "std_perplexity": 0.75,
            "mean_exact_match": 0.82,
            "std_exact_match": 0.03,
            "n_seeds": 5,
            "seed_values": [
                {"seed": 0, "perplexity": 12.0, "exact_match": 0.80},
                {"seed": 1, "perplexity": 13.0, "exact_match": 0.84}
            ]
        }
        output_file = tmp_path / "aggregated.json"
        
        save_aggregated_results(aggregated, str(output_file))
        
        with open(output_file, 'r') as f:
            saved_data = json.load(f)
        
        assert "mean_perplexity" in saved_data
        assert "std_perplexity" in saved_data
        assert "mean_exact_match" in saved_data
        assert "std_exact_match" in saved_data
        assert "n_seeds" in saved_data
        assert "seed_values" in saved_data
        assert isinstance(saved_data["mean_perplexity"], float)
        assert isinstance(saved_data["std_perplexity"], float)
        assert isinstance(saved_data["n_seeds"], int)
        assert isinstance(saved_data["seed_values"], list)
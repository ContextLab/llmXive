"""
Unit tests for statistical_summary.py module.
"""
import os
import tempfile
import yaml
from pathlib import Path
import pytest
from datetime import datetime

from src.evaluation.statistical_summary import (
    create_empty_summary,
    save_statistical_summary,
    load_statistical_summary,
    add_task_result,
    update_aggregate_stats,
    generate_summary_from_analysis
)


class TestStatisticalSummary:
    """Tests for statistical summary persistence functions."""

    def test_create_empty_summary_structure(self):
        """Verify empty summary has correct schema structure."""
        summary = create_empty_summary()
        
        assert "task_results" in summary
        assert "aggregate_stats" in summary
        assert isinstance(summary["task_results"], list)
        assert len(summary["task_results"]) == 0
        
        stats = summary["aggregate_stats"]
        assert stats["mean_accuracy_diff"] is None
        assert stats["p_value"] is None
        assert stats["effect_size"] is None
        assert stats["ci_lower"] is None
        assert stats["ci_upper"] is None

    def test_add_task_result(self):
        """Test adding a single task result."""
        summary = create_empty_summary()
        summary = add_task_result(
            summary,
            task_id="T001",
            accuracy=0.85,
            condition="heterogeneous"
        )
        
        assert len(summary["task_results"]) == 1
        entry = summary["task_results"][0]
        assert entry["task_id"] == "T001"
        assert entry["accuracy"] == 0.85
        assert entry["condition"] == "heterogeneous"
        assert "timestamp" in entry

    def test_add_multiple_task_results(self):
        """Test adding multiple results for different tasks/conditions."""
        summary = create_empty_summary()
        summary = add_task_result(summary, "T001", 0.85, "heterogeneous")
        summary = add_task_result(summary, "T001", 0.82, "unified")
        summary = add_task_result(summary, "T002", 0.91, "heterogeneous")
        
        assert len(summary["task_results"]) == 3
        conditions = [r["condition"] for r in summary["task_results"]]
        assert "heterogeneous" in conditions
        assert "unified" in conditions

    def test_update_aggregate_stats(self):
        """Test updating aggregate statistics."""
        summary = create_empty_summary()
        summary = update_aggregate_stats(
            summary,
            mean_accuracy_diff=0.03,
            p_value=0.02,
            effect_size=0.5,
            ci_lower=0.01,
            ci_upper=0.05
        )
        
        stats = summary["aggregate_stats"]
        assert stats["mean_accuracy_diff"] == 0.03
        assert stats["p_value"] == 0.02
        assert stats["effect_size"] == 0.5
        assert stats["ci_lower"] == 0.01
        assert stats["ci_upper"] == 0.05

    def test_save_and_load_yaml(self):
        """Test round-trip save and load of YAML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_summary.yaml")
            
            # Create and save
            summary = create_empty_summary()
            summary = add_task_result(summary, "T001", 0.90, "heterogeneous")
            summary = update_aggregate_stats(
                summary, 0.05, 0.01, 0.6, 0.02, 0.08
            )
            
            save_statistical_summary(summary, output_path)
            
            # Load and verify
            loaded = load_statistical_summary(output_path)
            assert loaded is not None
            assert len(loaded["task_results"]) == 1
            assert loaded["aggregate_stats"]["p_value"] == 0.01
            assert "metadata" in loaded
            assert "created_at" in loaded["metadata"]

    def test_generate_summary_from_analysis(self):
        """Test generating summary from raw analysis data."""
        task_results = [
            {"task_id": "T001", "accuracy": 0.88, "condition": "hetero"},
            {"task_id": "T001", "accuracy": 0.84, "condition": "unified"}
        ]
        analysis = {
            "mean_accuracy_diff": 0.04,
            "p_value": 0.03,
            "effect_size": 0.4,
            "ci_lower": 0.01,
            "ci_upper": 0.07
        }
        
        summary = generate_summary_from_analysis(task_results, analysis)
        
        assert len(summary["task_results"]) == 2
        assert summary["aggregate_stats"]["mean_accuracy_diff"] == 0.04
        assert summary["aggregate_stats"]["p_value"] == 0.03

    def test_load_nonexistent_file(self):
        """Test loading a file that doesn't exist returns None."""
        result = load_statistical_summary("/tmp/this_file_does_not_exist_12345.yaml")
        assert result is None

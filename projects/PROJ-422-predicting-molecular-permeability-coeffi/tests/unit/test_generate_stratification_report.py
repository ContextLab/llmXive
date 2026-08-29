"""
Unit tests for code/analysis/generate_stratification_report.py
"""
import json
import tempfile
from pathlib import Path
import pytest
from datetime import datetime

# Import functions to test
from analysis.generate_stratification_report import (
    load_split_metadata,
    load_distribution_stats,
    format_distribution,
    generate_report
)

class TestLoadSplitMetadata:
    def test_load_valid_metadata(self, tmp_path):
        """Test loading valid split metadata."""
        metadata = {
            "split_strategy": "stratified",
            "stratification_column": "polymer_type",
            "retention_rate": 0.98,
            "total_rows": 1000,
            "train_rows": 800,
            "test_rows": 200,
            "config_mode": "experimental"
        }
        
        metadata_path = tmp_path / "split_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)
        
        result = load_split_metadata(metadata_path)
        
        assert result == metadata
        assert result["split_strategy"] == "stratified"
        assert result["retention_rate"] == 0.98

    def test_load_missing_file(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        metadata_path = tmp_path / "nonexistent.json"
        
        with pytest.raises(FileNotFoundError):
            load_split_metadata(metadata_path)

    def test_load_invalid_json(self, tmp_path):
        """Test that JSONDecodeError is raised for invalid JSON."""
        metadata_path = tmp_path / "invalid.json"
        with open(metadata_path, 'w') as f:
            f.write("not valid json")
        
        with pytest.raises(json.JSONDecodeError):
            load_split_metadata(metadata_path)

class TestLoadDistributionStats:
    def test_load_valid_stats(self, tmp_path):
        """Test loading valid distribution statistics."""
        stats = {
            "classes": ["A", "B", "C"],
            "train_distribution": {"A": 0.33, "B": 0.34, "C": 0.33},
            "test_distribution": {"A": 0.34, "B": 0.33, "C": 0.33},
            "max_diff": 0.01,
            "threshold": 0.05
        }
        
        stats_path = tmp_path / "distribution_stats.json"
        with open(stats_path, 'w') as f:
            json.dump(stats, f)
        
        result = load_distribution_stats(stats_path)
        
        assert result == stats
        assert result["max_diff"] == 0.01

    def test_load_missing_file_returns_empty(self, tmp_path):
        """Test that missing stats file returns empty/default stats."""
        stats_path = tmp_path / "nonexistent.json"
        
        result = load_distribution_stats(stats_path)
        
        assert result["classes"] == []
        assert result["train_distribution"] == {}
        assert result["test_distribution"] == {}
        assert result["max_diff"] == 0.0
        assert "note" in result

class TestFormatDistribution:
    def test_format_distribution_table(self):
        """Test that distribution table is formatted correctly."""
        train_dist = {"A": 0.5, "B": 0.5}
        test_dist = {"A": 0.45, "B": 0.55}
        classes = ["A", "B"]
        
        result = format_distribution(train_dist, test_dist, classes)
        
        assert "| Class |" in result
        assert "|-------|" in result
        assert "| A |" in result
        assert "| B |" in result
        assert "0.5000" in result
        assert "0.4500" in result
        assert "0.5500" in result
        assert "0.0500" in result  # Difference

    def test_format_distribution_missing_classes(self):
        """Test handling of missing class in distribution."""
        train_dist = {"A": 0.5}
        test_dist = {"B": 0.5}
        classes = ["A", "B"]
        
        result = format_distribution(train_dist, test_dist, classes)
        
        assert "| A |" in result
        assert "| B |" in result
        # A should have 0.0000 in test
        assert "0.0000" in result

class TestGenerateReport:
    def test_generate_stratified_report(self):
        """Test report generation for stratified split."""
        metadata = {
            "split_strategy": "stratified",
            "stratification_column": "polymer_type",
            "retention_rate": 0.98,
            "total_rows": 1000,
            "train_rows": 800,
            "test_rows": 200,
            "config_mode": "experimental"
        }
        
        distribution_stats = {
            "classes": ["A", "B"],
            "train_distribution": {"A": 0.5, "B": 0.5},
            "test_distribution": {"A": 0.5, "B": 0.5},
            "max_diff": 0.0,
            "threshold": 0.05
        }
        
        report = generate_report(metadata, distribution_stats)
        
        assert "# Stratification Report" in report
        assert "STRATIFIED" in report
        assert "polymer_type" in report
        assert "98%" in report
        assert "Distribution Check PASSED" in report
        assert "| Class |" in report

    def test_generate_random_report(self):
        """Test report generation for random split."""
        metadata = {
            "split_strategy": "random",
            "retention_rate": 0.95,
            "total_rows": 1000,
            "train_rows": 800,
            "test_rows": 200,
            "warning": "Stratification skipped due to missing metadata"
        }
        
        distribution_stats = {
            "classes": [],
            "train_distribution": {},
            "test_distribution": {},
            "max_diff": 0.0,
            "threshold": 0.05,
            "note": "No stratification performed"
        }
        
        report = generate_report(metadata, distribution_stats)
        
        assert "# Stratification Report" in report
        assert "RANDOM" in report
        assert "Warning" in report
        assert "Random split" in report
        assert "Distribution Note" in report

    def test_generate_report_with_failed_check(self):
        """Test report generation when distribution check fails."""
        metadata = {
            "split_strategy": "stratified",
            "stratification_column": "polymer_type",
            "retention_rate": 0.98,
            "total_rows": 1000,
            "train_rows": 800,
            "test_rows": 200,
            "config_mode": "experimental"
        }
        
        distribution_stats = {
            "classes": ["A", "B"],
            "train_distribution": {"A": 0.8, "B": 0.2},
            "test_distribution": {"A": 0.4, "B": 0.6},
            "max_diff": 0.4,
            "threshold": 0.05
        }
        
        report = generate_report(metadata, distribution_stats)
        
        assert "Distribution Check FAILED" in report
        assert "0.4000" in report  # The large difference

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
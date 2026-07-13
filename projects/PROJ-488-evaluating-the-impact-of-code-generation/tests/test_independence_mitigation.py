"""
Tests for independence_mitigation module (Task T027).
"""
import json
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd
import numpy as np

from independence_mitigation import (
    load_processed_snippets,
    subsample_by_repository,
    apply_cluster_robust_se,
    write_independence_report,
    run_independence_mitigation
)


class TestSubsampleByRepository:
    """Tests for subsample_by_repository function."""

    def test_basic_subsample(self):
        """Test basic subsampling functionality."""
        snippets = [
            {"id": "1", "repo": "repo_a", "code": "print(1)"},
            {"id": "2", "repo": "repo_a", "code": "print(2)"},
            {"id": "3", "repo": "repo_b", "code": "print(3)"},
            {"id": "4", "repo": "repo_c", "code": "print(4)"},
            {"id": "5", "repo": "repo_c", "code": "print(5)"},
            {"id": "6", "repo": "repo_c", "code": "print(6)"},
        ]
        
        result = subsample_by_repository(snippets, seed=42)
        
        # Should have exactly 3 snippets (one per repo)
        assert len(result) == 3
        
        # Should have unique repos
        repos = set(s["repo"] for s in result)
        assert len(repos) == 3
        assert repos == {"repo_a", "repo_b", "repo_c"}

    def test_single_snippet_per_repo(self):
        """Test that we get exactly one snippet per repository."""
        snippets = [
            {"id": str(i), "repo": f"repo_{i % 3}", "code": f"code_{i}"}
            for i in range(100)
        ]
        
        result = subsample_by_repository(snippets, seed=123)
        
        repos = [s["repo"] for s in result]
        assert len(repos) == len(set(repos))  # All unique
        assert len(result) == 3  # 3 unique repos

    def test_empty_input(self):
        """Test handling of empty input."""
        result = subsample_by_repository([], seed=42)
        assert len(result) == 0

    def test_unknown_repo_handling(self):
        """Test handling of missing repo field."""
        snippets = [
            {"id": "1", "code": "print(1)"},
            {"id": "2", "repo": "repo_a", "code": "print(2)"},
        ]
        
        result = subsample_by_repository(snippets, seed=42)
        
        # Should still work, grouping unknown repos together
        assert len(result) <= 2  # At most 2 groups (unknown + repo_a)


class TestLoadProcessedSnippets:
    """Tests for load_processed_snippets function."""

    def test_load_from_json_files(self, tmp_path):
        """Test loading snippets from JSON files."""
        processed_dir = tmp_path / "processed"
        processed_dir.mkdir()
        
        # Create test JSON files
        data1 = [
            {"id": "1", "code": "print(1)"},
            {"id": "2", "code": "print(2)"}
        ]
        data2 = [
            {"id": "3", "code": "print(3)"}
        ]
        
        with open(processed_dir / "test1.json", 'w') as f:
            json.dump(data1, f)
        with open(processed_dir / "test2.json", 'w') as f:
            json.dump(data2, f)
        
        result = load_processed_snippets(tmp_path)
        
        assert len(result) == 3
        assert result[0]["id"] == "1"
        assert result[2]["id"] == "3"

    def test_load_from_nested_structure(self, tmp_path):
        """Test loading from nested JSON structure."""
        processed_dir = tmp_path / "processed"
        processed_dir.mkdir()
        
        data = {
            "snippets": [
                {"id": "1", "code": "print(1)"},
                {"id": "2", "code": "print(2)"}
            ]
        }
        
        with open(processed_dir / "nested.json", 'w') as f:
            json.dump(data, f)
        
        result = load_processed_snippets(tmp_path)
        
        assert len(result) == 2

    def test_missing_directory(self, tmp_path):
        """Test handling of missing processed directory."""
        result = load_processed_snippets(tmp_path / "nonexistent")
        assert len(result) == 0


class TestClusterRobustSE:
    """Tests for apply_cluster_robust_se function."""

    def test_basic_cluster_robust(self):
        """Test basic cluster-robust SE calculation."""
        df = pd.DataFrame({
            "repo": ["A", "A", "B", "B", "C", "C"],
            "metric1": [1, 2, 3, 4, 5, 6],
            "metric2": [10, 20, 30, 40, 50, 60]
        })
        
        result = apply_cluster_robust_se(df, cluster_field="repo", metric_cols=["metric1"])
        
        # Should have statistics for 3 clusters
        assert "metric1" in result.index or result.shape[0] == 3

    def test_single_cluster(self):
        """Test handling of single cluster."""
        df = pd.DataFrame({
            "repo": ["A", "A", "A"],
            "metric1": [1, 2, 3]
        })
        
        result = apply_cluster_robust_se(df, cluster_field="repo")
        
        # Should still compute statistics
        assert result is not None


class TestWriteIndependenceReport:
    """Tests for write_independence_report function."""

    def test_write_subsample_report(self, tmp_path):
        """Test writing subsample report."""
        output_path = tmp_path / "report.md"
        
        write_independence_report(
            output_path,
            method="subsample",
            original_count=1000,
            final_count=100,
            cluster_count=100,
            details={"test": "value"}
        )
        
        assert output_path.exists()
        content = output_path.read_text()
        assert "subsample" in content.lower()
        assert "1000" in content
        assert "100" in content

    def test_write_cluster_robust_report(self, tmp_path):
        """Test writing cluster-robust report."""
        output_path = tmp_path / "report.md"
        
        write_independence_report(
            output_path,
            method="cluster_robust",
            original_count=1000,
            final_count=1000,
            details={"reason": "test"}
        )
        
        assert output_path.exists()
        content = output_path.read_text()
        assert "cluster-robust" in content.lower()


class TestRunIndependenceMitigation:
    """Tests for run_independence_mitigation function."""

    def test_full_workflow_with_subsample(self, tmp_path):
        """Test full workflow with subsampling."""
        data_dir = tmp_path / "data"
        processed_dir = data_dir / "processed"
        processed_dir.mkdir(parents=True)
        
        # Create test snippets
        snippets = [
            {"id": str(i), "repo": f"repo_{i % 5}", "code": f"code_{i}"}
            for i in range(50)
        ]
        
        with open(processed_dir / "test.json", 'w') as f:
            json.dump(snippets, f)
        
        output_dir = tmp_path / "results"
        
        result = run_independence_mitigation(data_dir, output_dir)
        
        assert result["success"] is True
        assert result["method"] == "subsample"
        assert result["original_count"] == 50
        assert result["final_count"] == 5  # 5 unique repos
        
        # Check report was created
        report_path = output_dir / "independence.md"
        assert report_path.exists()

    def test_full_workflow_cluster_robust_fallback(self, tmp_path):
        """Test full workflow with cluster-robust fallback."""
        data_dir = tmp_path / "data"
        processed_dir = data_dir / "processed"
        processed_dir.mkdir(parents=True)
        
        # Create snippets without repo field
        snippets = [
            {"id": str(i), "code": f"code_{i}"}
            for i in range(10)
        ]
        
        with open(processed_dir / "test.json", 'w') as f:
            json.dump(snippets, f)
        
        output_dir = tmp_path / "results"
        
        result = run_independence_mitigation(data_dir, output_dir)
        
        assert result["success"] is True
        assert result["method"] == "cluster_robust"

    def test_force_cluster_robust(self, tmp_path):
        """Test forcing cluster-robust even with repo metadata."""
        data_dir = tmp_path / "data"
        processed_dir = data_dir / "processed"
        processed_dir.mkdir(parents=True)
        
        snippets = [
            {"id": str(i), "repo": f"repo_{i % 3}", "code": f"code_{i}"}
            for i in range(15)
        ]
        
        with open(processed_dir / "test.json", 'w') as f:
            json.dump(snippets, f)
        
        output_dir = tmp_path / "results"
        
        result = run_independence_mitigation(data_dir, output_dir, force_cluster_robust=True)
        
        assert result["success"] is True
        assert result["method"] == "cluster_robust"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

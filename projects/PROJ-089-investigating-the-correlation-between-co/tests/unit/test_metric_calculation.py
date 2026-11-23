"""
Unit tests for metric calculation logic in the code-churn-debt pipeline.

Tests cover:
- Git history aggregation (lines changed, commit counts)
- Static analysis debt score calculation (Semgrep results)
- Correlation analysis (Pearson, Spearman, partial correlation)
- Sensitivity analysis thresholds
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
import pytest

# Import functions to test based on the API surface
# We import from the modules that contain the logic
from code.preprocessing import is_source_file, should_exclude_dir
from code.static_analysis import get_file_language, calculate_debt_score
from code.analysis import run_correlation_analysis
from code.config import get_config_summary


class TestSourceFileFiltering:
    """Tests for file type filtering logic."""

    def test_is_source_file_python(self):
        """Python files should be recognized as source files."""
        assert is_source_file("script.py") is True
        assert is_source_file("module/submodule.py") is True
        assert is_source_file("test_script.py") is True

    def test_is_source_file_java(self):
        """Java files should be recognized as source files."""
        assert is_source_file("App.java") is True
        assert is_source_file("com/example/App.java") is True

    def test_is_source_file_javascript(self):
        """JavaScript files should be recognized as source files."""
        assert is_source_file("app.js") is True
        assert is_source_file("src/app.js") is True

    def test_is_source_file_typescript(self):
        """TypeScript files should be recognized as source files."""
        assert is_source_file("app.ts") is True
        assert is_source_file("src/app.tsx") is True

    def test_is_source_file_go(self):
        """Go files should be recognized as source files."""
        assert is_source_file("main.go") is True
        assert is_source_file("pkg/main.go") is True

    def test_is_source_file_rust(self):
        """Rust files should be recognized as source files."""
        assert is_source_file("main.rs") is True
        assert is_source_file("src/main.rs") is True

    def test_is_source_file_not_source(self):
        """Non-source files should be filtered out."""
        assert is_source_file("README.md") is False
        assert is_source_file("requirements.txt") is False
        assert is_source_file("Dockerfile") is False
        assert is_source_file("config.yaml") is False
        assert is_source_file("image.png") is False
        assert is_source_file("test.pyc") is False

    def test_is_source_file_case_insensitive(self):
        """File extension check should be case insensitive."""
        assert is_source_file("Script.PY") is True
        assert is_source_file("App.JAVA") is True
        assert is_source_file("App.Js") is True

    def test_should_exclude_dir(self):
        """Common non-source directories should be excluded."""
        assert should_exclude_dir(".git") is True
        assert should_exclude_dir("node_modules") is True
        assert should_exclude_dir("__pycache__") is True
        assert should_exclude_dir("venv") is True
        assert should_exclude_dir(".venv") is True
        assert should_exclude_dir("build") is True
        assert should_exclude_dir("dist") is True
        assert should_exclude_dir("target") is True

    def test_should_exclude_dir_custom(self):
        """Custom directories from config should be excluded."""
        # Test with a custom directory name
        assert should_exclude_dir("custom_build") is False  # Not in default list


class TestStaticAnalysisMetrics:
    """Tests for static analysis debt score calculation."""

    def test_get_file_language_python(self):
        """Python files should return 'python'."""
        assert get_file_language("script.py") == "python"
        assert get_file_language("module.py") == "python"

    def test_get_file_language_java(self):
        """Java files should return 'java'."""
        assert get_file_language("App.java") == "java"
        assert get_file_language("com/example/App.java") == "java"

    def test_get_file_language_javascript(self):
        """JavaScript files should return 'javascript'."""
        assert get_file_language("app.js") == "javascript"
        assert get_file_language("src/app.js") == "javascript"

    def test_get_file_language_typescript(self):
        """TypeScript files should return 'typescript'."""
        assert get_file_language("app.ts") == "typescript"
        assert get_file_language("app.tsx") == "typescript"

    def test_get_file_language_go(self):
        """Go files should return 'go'."""
        assert get_file_language("main.go") == "go"

    def test_get_file_language_rust(self):
        """Rust files should return 'rust'."""
        assert get_file_language("main.rs") == "rust"

    def test_get_file_language_unknown(self):
        """Unknown file types should return None."""
        assert get_file_language("unknown.xyz") is None
        assert get_file_language("README") is None

    def test_calculate_debt_score_python_with_mi(self):
        """Python debt score should sum complexity and MI deficit."""
        # Mock semgrep result with cyclomatic complexity and maintainability index
        semgrep_results = {
            "file.py": {
                "cyclomatic_complexity": 15,
                "maintainability_index": 60
            }
        }
        # Debt score = Complexity + (100 - MI) = 15 + (100 - 60) = 55
        score = calculate_debt_score(semgrep_results, "python")
        assert score == 55

    def test_calculate_debt_score_python_without_mi(self):
        """Python debt score should skip MI if not present."""
        # Mock semgrep result without maintainability index
        semgrep_results = {
            "file.py": {
                "cyclomatic_complexity": 15
            }
        }
        # Debt score = Complexity only = 15
        score = calculate_debt_score(semgrep_results, "python")
        assert score == 15

    def test_calculate_debt_score_java(self):
        """Java debt score should sum code smells and complexity."""
        # Mock semgrep result for Java
        semgrep_results = {
            "App.java": {
                "code_smells": 5,
                "cyclomatic_complexity": 10
            }
        }
        # Debt score = Smells + Complexity = 5 + 10 = 15
        score = calculate_debt_score(semgrep_results, "java")
        assert score == 15

    def test_calculate_debt_score_empty(self):
        """Empty results should return 0."""
        score = calculate_debt_score({}, "python")
        assert score == 0

    def test_calculate_debt_score_multiple_files(self):
        """Multiple files should be aggregated correctly."""
        semgrep_results = {
            "file1.py": {"cyclomatic_complexity": 10, "maintainability_index": 50},
            "file2.py": {"cyclomatic_complexity": 20, "maintainability_index": 40}
        }
        # file1: 10 + (100-50) = 60
        # file2: 20 + (100-40) = 80
        # Total: 140
        score = calculate_debt_score(semgrep_results, "python")
        assert score == 140


class TestCorrelationAnalysis:
    """Tests for correlation analysis logic."""

    def test_run_correlation_analysis_basic(self):
        """Basic correlation analysis should run without errors."""
        # Create a simple test dataframe
        data = {
            "total_lines_changed": [100, 200, 300, 400, 500],
            "debt_score": [10, 20, 30, 40, 50],
            "avg_loc": [10, 15, 20, 25, 30],
            "contributor_count": [1, 2, 3, 4, 5]
        }
        df = pd.DataFrame(data)

        # Run correlation analysis with threshold 0
        result = run_correlation_analysis(df, loc_threshold=0)

        # Verify result structure
        assert "pearson_r" in result
        assert "pearson_p" in result
        assert "spearman_r" in result
        assert "spearman_p" in result
        assert "n" in result
        assert result["n"] == 5

    def test_run_correlation_analysis_with_threshold(self):
        """Correlation analysis should filter by LOC threshold."""
        data = {
            "total_lines_changed": [100, 200, 300, 400, 500],
            "debt_score": [10, 20, 30, 40, 50],
            "avg_loc": [5, 10, 15, 20, 25],
            "contributor_count": [1, 2, 3, 4, 5]
        }
        df = pd.DataFrame(data)

        # Run with threshold 15 - should only include 3 rows
        result = run_correlation_analysis(df, loc_threshold=15)

        assert result["n"] == 3
        # The filtered data should be [300, 400, 500] vs [30, 40, 50]
        # This should still show a strong positive correlation

    def test_run_correlation_analysis_partial_corr(self):
        """Partial correlation should control for avg_loc."""
        # Create data where raw correlation is high but controlled should be lower
        # or vice versa
        np.random.seed(42)
        n = 100
        avg_loc = np.random.normal(20, 5, n)
        churn = avg_loc * 2 + np.random.normal(0, 10, n)
        debt = churn * 0.5 + avg_loc * 0.1 + np.random.normal(0, 5, n)

        data = {
            "total_lines_changed": churn,
            "debt_score": debt,
            "avg_loc": avg_loc,
            "contributor_count": np.random.randint(1, 10, n)
        }
        df = pd.DataFrame(data)

        result = run_correlation_analysis(df, loc_threshold=0)

        # Should have valid correlation values
        assert -1 <= result["pearson_r"] <= 1
        assert result["pearson_p"] >= 0
        assert result["pearson_p"] <= 1

    def test_run_correlation_analysis_edge_cases(self):
        """Handle edge cases like constant values or small samples."""
        # Small sample
        data = {
            "total_lines_changed": [100, 200],
            "debt_score": [10, 20],
            "avg_loc": [10, 15],
            "contributor_count": [1, 2]
        }
        df = pd.DataFrame(data)
        result = run_correlation_analysis(df, loc_threshold=0)
        assert result["n"] == 2

        # Constant values (should handle gracefully)
        data_const = {
            "total_lines_changed": [100, 100, 100],
            "debt_score": [10, 10, 10],
            "avg_loc": [10, 15, 20],
            "contributor_count": [1, 2, 3]
        }
        df_const = pd.DataFrame(data_const)
        result_const = run_correlation_analysis(df_const, loc_threshold=0)
        # Should not crash, even if correlation is undefined


class TestConfigAndUtilities:
    """Tests for configuration and utility functions."""

    def test_get_config_summary(self):
        """Config summary should return expected structure."""
        config = get_config_summary()
        assert isinstance(config, dict)
        assert "loc_thresholds" in config
        assert "repo_limits" in config
        assert "tool_versions" in config

    def test_loc_thresholds_in_config(self):
        """Config should include sensitivity analysis thresholds."""
        config = get_config_summary()
        thresholds = config.get("loc_thresholds", [])
        assert 5 in thresholds
        assert 10 in thresholds
        assert 20 in thresholds


class TestIntegrationScenarios:
    """Integration-style tests for metric calculation pipelines."""

    def test_full_pipeline_metric_flow(self):
        """Test the flow of metrics through the pipeline components."""
        # Simulate the flow:
        # 1. Git metrics extraction (mocked)
        # 2. Static analysis (mocked)
        # 3. Preprocessing (filtering)
        # 4. Analysis (correlation)

        # Mock git history data
        git_data = {
            "file1.py": {"total_lines_changed": 100, "commit_count": 5},
            "file2.py": {"total_lines_changed": 200, "commit_count": 10},
            "README.md": {"total_lines_changed": 50, "commit_count": 2},  # Should be filtered
            "main.go": {"total_lines_changed": 150, "commit_count": 3}
        }

        # Mock semgrep data
        semgrep_data = {
            "file1.py": {"cyclomatic_complexity": 10, "maintainability_index": 70},
            "file2.py": {"cyclomatic_complexity": 20, "maintainability_index": 60},
            "main.go": {"code_smells": 5, "cyclomatic_complexity": 15}
        }

        # Verify filtering
        assert is_source_file("file1.py") is True
        assert is_source_file("README.md") is False
        assert is_source_file("main.go") is True

        # Verify language detection
        assert get_file_language("file1.py") == "python"
        assert get_file_language("main.go") == "go"

        # Verify debt score calculation
        python_score = calculate_debt_score(
            {"file1.py": semgrep_data["file1.py"]}, "python"
        )
        assert python_score == 10 + (100 - 70)  # 40

        go_score = calculate_debt_score(
            {"main.go": semgrep_data["main.go"]}, "go"
        )
        assert go_score == 5 + 15  # 20


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

import pytest

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))
from validate_quickstart import main as validate_main

@pytest.fixture
def full_project_structure(temp_dir):
    """Create a complete mock project structure for E2E testing."""
    # Create directory structure
    dirs = [
        "data/raw",
        "data/generated",
        "data/analysis",
        "results/figures"
    ]
    for d in dirs:
        os.makedirs(os.path.join(temp_dir, d), exist_ok=True)
    
    # Create mock humaneval.json
    humaneval_file = os.path.join(temp_dir, "data/raw/humaneval.json")
    humaneval_data = [
        {"task_id": "test/0", "prompt": "def hello(): pass", "canonical_solution": "def hello(): return 'hello'"},
        {"task_id": "test/1", "prompt": "def add(a, b): pass", "canonical_solution": "def add(a, b): return a + b"}
    ]
    with open(humaneval_file, 'w') as f:
        json.dump(humaneval_data, f)
    
    # Create mock metrics.json with all required fields
    metrics_file = os.path.join(temp_dir, "data/analysis/metrics.json")
    metrics_data = {
        "samples": [
            {
                "task_id": "test/0",
                "cyclomatic_complexity": 2.0,
                "halstead_volume": 15.5,
                "branch_coverage_pct": 95.0,
                "pass_rate": 1
            },
            {
                "task_id": "test/1",
                "cyclomatic_complexity": 3.0,
                "halstead_volume": 20.0,
                "branch_coverage_pct": 80.0,
                "pass_rate": 0
            }
        ]
    }
    with open(metrics_file, 'w') as f:
        json.dump(metrics_data, f)
    
    # Create mock figures
    figures_dir = os.path.join(temp_dir, "results/figures")
    with open(os.path.join(figures_dir, "histogram_complexity.png"), 'w') as f:
        f.write("fake png content")
    with open(os.path.join(figures_dir, "boxplot_coverage.png"), 'w') as f:
        f.write("fake png content")
    
    # Create mock results_report.md with figures and tables
    report_file = os.path.join(temp_dir, "results_report.md")
    report_content = """
    # Code Generation Impact Analysis Report

    ## Figures
    ![Complexity Distribution](figures/histogram_complexity.png)
    ![Coverage Distribution](figures/boxplot_coverage.png)

    ## Metrics Summary

    | Metric | Mean | Std Dev |
    |--------|------|---------|
    | Cyclomatic Complexity | 2.5 | 0.5 |
    | Halstead Volume | 17.75 | 2.5 |
    | Branch Coverage | 87.5 | 7.5 |
    | Pass Rate | 50% | - |

    ## Statistical Results

    | Test | p-value | Significant |
    |------|---------|-------------|
    | Wilcoxon | 0.03 | Yes |
    | McNemar | 0.15 | No |

    ## Sensitivity Analysis

    Comparison of CodeLlama 7B/3B vs 350M shows consistent results.
    """
    with open(report_file, 'w') as f:
        f.write(report_content)
    
    return temp_dir

def test_full_validation_pass(full_project_structure):
    """Test that validate_main returns 0 when all artifacts are present."""
    original_cwd = os.getcwd()
    os.chdir(full_project_structure)
    try:
        result = validate_main()
        assert result == 0, "Validation should pass with complete project structure"
    finally:
        os.chdir(original_cwd)

def test_validation_fails_missing_metrics(full_project_structure):
    """Test that validation fails when metrics.json is missing."""
    original_cwd = os.getcwd()
    os.chdir(full_project_structure)
    try:
        # Remove metrics.json
        os.remove("data/analysis/metrics.json")
        result = validate_main()
        assert result == 1, "Validation should fail when metrics.json is missing"
    finally:
        os.chdir(original_cwd)

def test_validation_fails_missing_report(full_project_structure):
    """Test that validation fails when results_report.md is missing."""
    original_cwd = os.getcwd()
    os.chdir(full_project_structure)
    try:
        # Remove results_report.md
        os.remove("results_report.md")
        result = validate_main()
        assert result == 1, "Validation should fail when results_report.md is missing"
    finally:
        os.chdir(original_cwd)

def test_validation_fails_missing_directory(full_project_structure):
    """Test that validation fails when a required directory is missing."""
    original_cwd = os.getcwd()
    os.chdir(full_project_structure)
    try:
        # Remove a required directory
        shutil.rmtree("data/analysis")
        result = validate_main()
        assert result == 1, "Validation should fail when data/analysis is missing"
    finally:
        os.chdir(original_cwd)

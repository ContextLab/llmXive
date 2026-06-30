import os
import json
import tempfile
import csv
from pathlib import Path
import pytest
import numpy as np

# Import the function we are testing
from analyzer import generate_stats_summary, run_statistical_analysis, pair_llm_human_results, load_coverage_reports

@pytest.fixture
def temp_reports_dir():
    """Create a temporary directory with mock coverage reports."""
    with tempfile.TemporaryDirectory() as tmpdir:
        reports_dir = Path(tmpdir)
        # Create mock LLM and Human reports for a few tasks
        tasks = ["task_001", "task_002", "task_003"]
        
        for task_id in tasks:
            # LLM Report
            llm_report = {
                "task_id": task_id,
                "source": "llm",
                "line_coverage": 0.85,
                "branch_coverage": 0.70,
                "status": "success"
            }
            with open(reports_dir / f"{task_id}_llm.json", 'w') as f:
                json.dump(llm_report, f)
            
            # Human Report
            human_report = {
                "task_id": task_id,
                "source": "human",
                "line_coverage": 0.90,
                "branch_coverage": 0.80,
                "status": "success"
            }
            with open(reports_dir / f"{task_id}_human.json", 'w') as f:
                json.dump(human_report, f)

        yield str(reports_dir)

def test_generate_stats_summary_creates_file(temp_reports_dir, tmp_path):
    """Test that T026 implementation creates the stats_summary.csv file."""
    output_file = tmp_path / "stats_summary.csv"
    
    generate_stats_summary(temp_reports_dir, str(output_file))
    
    assert output_file.exists(), "stats_summary.csv was not created"
    
    with open(output_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 1, "Expected exactly one row of summary statistics"
    
    row = rows[0]
    required_columns = ["mean_llm", "mean_human", "mean_diff", "p_value", "cohen_d", "test_type"]
    for col in required_columns:
        assert col in row, f"Missing column: {col}"
    
    # Verify values are numeric (except test_type)
    assert row["test_type"] in ["t-test", "Wilcoxon"]
    assert float(row["mean_llm"]) < 1.0
    assert float(row["mean_human"]) < 1.0
    # Mean diff should be negative if human > llm (0.90 - 0.85 = 0.05, so llm - human = -0.05)
    # Wait, my logic in analyzer: diffs.append(llm_val - human_val) -> 0.85 - 0.90 = -0.05
    # So mean_diff should be around -0.05
    assert float(row["mean_diff"]) < 0

def test_load_coverage_reports_filters_failed(temp_reports_dir):
    """Test that failed reports are ignored."""
    # Add a failed report
    with open(Path(temp_reports_dir) / "failed_task_llm.json", 'w') as f:
        json.dump({"task_id": "failed_task", "source": "llm", "status": "failed"}, f)
    
    reports = load_coverage_reports(temp_reports_dir)
    # Should have 3 pairs * 2 (6) - 0 failed = 6 reports
    # Actually, load_coverage_reports returns a list of dicts.
    # We added 3 pairs (6 files) + 1 failed file.
    # The failed file should be skipped.
    assert len(reports) == 6, "Failed reports should be excluded"

def test_pair_llm_human_results_logic(temp_reports_dir):
    """Test the pairing logic."""
    reports = load_coverage_reports(temp_reports_dir)
    pairs = pair_llm_human_results(reports)
    
    assert len(pairs) == 3, "Expected 3 paired tasks"
    
    for pair in pairs:
        assert "task_id" in pair
        assert "llm" in pair
        assert "human" in pair
        assert pair["llm"]["source"] == "llm"
        assert pair["human"]["source"] == "human"

def test_run_statistical_analysis_insufficient_data():
    """Test handling of insufficient data."""
    # Empty list
    result = run_statistical_analysis([])
    assert result["mean_llm"] is None
    assert result["test_type"] == "N/A"
    
    # Single pair (not enough for t-test/wilcoxon)
    single_pair = [{"llm": {"line_coverage": 0.5}, "human": {"line_coverage": 0.6}}]
    result = run_statistical_analysis(single_pair)
    assert result["mean_llm"] is None # shapiro needs at least 3 usually, t-test needs 2
    # Actually scipy stats might throw or return nan if n < 2. 
    # My implementation checks len < 2.
    # Wait, t-test needs at least 2 samples. shapiro needs at least 3.
    # My code: if len < 2: return N/A. So single pair (n=1) -> N/A.
    assert result["test_type"] == "N/A"

def test_handles_n_a_values(temp_reports_dir, tmp_path):
    """Test that N/A branch coverage is handled correctly if we test branch_coverage."""
    # Modify one human report to have N/A branch coverage
    reports_path = Path(temp_reports_dir)
    human_file = reports_path / "task_001_human.json"
    with open(human_file, 'r') as f:
        data = json.load(f)
    data["branch_coverage"] = "N/A"
    with open(human_file, 'w') as f:
        json.dump(data, f)
    
    output_file = tmp_path / "stats_branch.csv"
    # Try to run analysis on branch_coverage
    generate_stats_summary(temp_reports_dir, str(output_file), metric="branch_coverage")
    
    with open(output_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # task_001 should be excluded from branch_coverage stats because human is N/A
    # We have 3 tasks. 1 is N/A. So 2 valid pairs.
    # The stats should be calculated on the remaining 2.
    assert len(rows) == 1
    # The values should reflect only the 2 valid tasks (task_002, task_003)
    # task_002: llm 0.7, human 0.8
    # task_003: llm 0.7, human 0.8
    # Mean diff = -0.1
    assert float(rows[0]["mean_diff"]) == -0.1

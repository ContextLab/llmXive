"""
Integration test to verify quickstart validation passes.
This test ensures that running the validation script produces the expected output.
"""
import subprocess
import sys
import os
from pathlib import Path

def test_quickstart_validation_runs_successfully():
    """
    Test that the quickstart validation script runs and passes.
    This verifies that all required artifacts are generated correctly.
    """
    project_root = Path(__file__).parent.parent.parent
    validator_script = project_root / "code" / "quickstart_validator.py"
    
    # Ensure the script exists
    assert validator_script.exists(), f"Validator script not found at {validator_script}"
    
    # Run the validator
    result = subprocess.run(
        [sys.executable, str(validator_script)],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    
    # Log output for debugging
    if result.returncode != 0:
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
    
    # Assert success
    assert result.returncode == 0, (
        f"Quickstart validation failed with return code {result.returncode}\n"
        f"STDERR: {result.stderr}\n"
        f"STDOUT: {result.stdout}"
    )

def test_artifacts_exist():
    """
    Test that all required artifacts exist on disk.
    """
    project_root = Path(__file__).parent.parent.parent
    
    required_paths = [
        project_root / "data" / "raw" / "qrels_robust04.json",
        project_root / "data" / "raw" / "qrels_web.json",
        project_root / "results" / "p_values" / "raw_p_values.csv",
        project_root / "results" / "mdes" / "mdes_summary.csv",
        project_root / "results" / "p_values" / "corrected_p_values.csv",
        project_root / "results" / "sensitivity" / "alpha_sweep.csv",
        project_root / "results" / "summary.csv",
    ]
    
    for path in required_paths:
        assert path.exists(), f"Required artifact missing: {path}"

def test_csv_files_have_correct_columns():
    """
    Test that CSV files have the expected columns.
    """
    import csv
    from pathlib import Path
    
    project_root = Path(__file__).parent.parent.parent
    
    required_columns = {
        "results/p_values/raw_p_values.csv": ["query_id", "metric", "p_value"],
        "results/mdes/mdes_summary.csv": ["metric", "mdes", "power", "ci_width"],
        "results/p_values/corrected_p_values.csv": ["query_id", "metric", "raw_p", "corrected_p", "is_significant"],
        "results/sensitivity/alpha_sweep.csv": ["alpha", "significant_count"],
        "results/summary.csv": ["query_id", "metric", "observed_score", "raw_p", "corrected_p", "mdes", "is_significant"],
    }
    
    for path_str, expected_cols in required_columns.items():
        file_path = project_root / path_str
        assert file_path.exists(), f"CSV file missing: {file_path}"
        
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames is not None, f"Empty CSV: {file_path}"
            
            missing = set(expected_cols) - set(reader.fieldnames)
            assert not missing, f"Missing columns in {file_path}: {missing}"
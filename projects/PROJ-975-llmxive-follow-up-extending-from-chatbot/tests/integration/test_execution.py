"""
Integration test for the full execution loop (500 tasks × 1 config).
Verifies that `data/results/experiment_log.csv` is created and contains
the correct structure and data types as defined in the experiment schema.
"""
import os
import json
import csv
import pytest
import subprocess
import sys
from pathlib import Path

# Project root is the parent of 'tests'
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_RESULTS = PROJECT_ROOT / "data" / "results"
CODE_DIR = PROJECT_ROOT / "code"

# Expected schema columns based on T004 and T021
EXPECTED_COLUMNS = [
    "task_id",
    "skill_id",
    "success",
    "latency",
    "tokens",
    "retrieval_precision",
    "retrieval_diversity",
    "pruning_risk_count",
    "library_size",
    "pruning_enabled",
]

@pytest.fixture(scope="module", autouse=True)
def setup_and_run_experiment():
    """
    Setup: Ensure data directories exist.
    Action: Run the data generation script to create inputs if missing.
            Then run the agent script for a subset or full run.
    """
    # Ensure directories exist
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    DATA_RESULTS.mkdir(parents=True, exist_ok=True)

    # Check if data exists; if not, generate it
    tasks_path = DATA_RAW / "tasks.json"
    skills_path = DATA_RAW / "skills.json"

    if not tasks_path.exists() or not skills_path.exists():
        print("Generating synthetic data for integration test...")
        # Run generate_data.py
        result = subprocess.run(
            [sys.executable, str(CODE_DIR / "generate_data.py")],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            pytest.fail(f"Data generation failed: {result.stderr}")

    # Run the agent experiment
    # We run the full 500 tasks as per the task description
    print("Running agent execution loop for integration test...")
    result = subprocess.run(
        [sys.executable, str(CODE_DIR / "agent.py")],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True
    )
    
    # The agent script might fail if dependencies aren't fully set up (e.g., logging),
    # but we proceed to check if the file was created or partially written.
    # If the agent script requires specific args not provided, we might need to adjust.
    # Assuming agent.py runs with defaults as per T019-T022.
    
    return result

def test_experiment_log_file_exists(setup_and_run_experiment):
    """Verifies that experiment_log.csv is created."""
    log_path = DATA_RESULTS / "experiment_log.csv"
    assert log_path.exists(), f"Expected {log_path} to be created by agent.py"

def test_experiment_log_header(setup_and_run_experiment):
    """Verifies the CSV header matches the expected schema."""
    log_path = DATA_RESULTS / "experiment_log.csv"
    with open(log_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
    
    # Check that all expected columns are present
    assert set(header) == set(EXPECTED_COLUMNS), \
        f"Header mismatch. Expected {EXPECTED_COLUMNS}, got {header}"

def test_experiment_log_row_count(setup_and_run_experiment):
    """Verifies that the log contains data rows (expecting 500 tasks)."""
    log_path = DATA_RESULTS / "experiment_log.csv"
    with open(log_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # We expect 500 tasks to be processed
    # Note: If the agent fails early, this might be 0. 
    # But the task implies a successful run of 500 tasks.
    assert len(rows) > 0, "No data rows found in experiment_log.csv"
    
    # Ideally 500, but we assert > 0 for the integration test to pass 
    # if the script ran partially. For strict compliance:
    # assert len(rows) == 500, f"Expected 500 rows, found {len(rows)}"
    
    # Let's be strict as per "500 tasks" requirement
    assert len(rows) == 500, f"Expected 500 rows, found {len(rows)}"

def test_experiment_log_data_types(setup_and_run_experiment):
    """Verifies that data types in the CSV are correct."""
    log_path = DATA_RESULTS / "experiment_log.csv"
    with open(log_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            # success should be boolean-like (True/False)
            assert row["success"] in ["True", "False"], \
                f"Row {i}: 'success' must be True/False, got {row['success']}"
            
            # latency and tokens should be numeric
            try:
                float(row["latency"])
                int(row["tokens"])
            except ValueError:
                pytest.fail(f"Row {i}: 'latency' or 'tokens' is not numeric")
            
            # retrieval_precision and retrieval_diversity should be floats
            try:
                float(row["retrieval_precision"])
                float(row["retrieval_diversity"])
            except ValueError:
                pytest.fail(f"Row {i}: metrics are not numeric")
            
            # pruning_risk_count should be int
            try:
                int(row["pruning_risk_count"])
            except ValueError:
                pytest.fail(f"Row {i}: 'pruning_risk_count' is not numeric")
            
            # library_size should be int
            try:
                int(row["library_size"])
            except ValueError:
                pytest.fail(f"Row {i}: 'library_size' is not numeric")
            
            # pruning_enabled should be boolean-like
            assert row["pruning_enabled"] in ["True", "False"], \
                f"Row {i}: 'pruning_enabled' must be True/False"

def test_experiment_log_content_validity(setup_and_run_experiment):
    """Verifies that specific values are within expected ranges."""
    log_path = DATA_RESULTS / "experiment_log.csv"
    with open(log_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Precision and Diversity should be between 0 and 1 (or at least non-negative)
            p = float(row["retrieval_precision"])
            d = float(row["retrieval_diversity"])
            assert 0.0 <= p <= 1.0, f"Precision {p} out of range [0, 1]"
            # Diversity is inverse variance, could be > 1, but should be >= 0
            assert d >= 0.0, f"Diversity {d} is negative"
            
            # Latency should be non-negative
            assert float(row["latency"]) >= 0.0, "Latency is negative"
            
            # Tokens should be positive
            assert int(row["tokens"]) > 0, "Tokens is not positive"
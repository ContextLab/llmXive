"""
Integration test for the full execution loop (500 tasks × 1 config).
Verifies that `experiment_log.csv` is created, flushed, and contains
the correct schema and data integrity after running the agent.
"""
import os
import sys
import json
import csv
import tempfile
import shutil
import pytest
from pathlib import Path

# Add project root to path to allow imports from code/
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "code"))

from config import get_experiment_config, get_seeds, pin_seeds
from logging_config import verify_log_file_exists
from generate_data import main as generate_data_main
from agent import main as agent_main

# Constants for test configuration
TEST_OUTPUT_DIR = "data/results"
TEST_RAW_DIR = "data/raw"
LOG_FILE_NAME = "experiment_log.csv"
SKILLS_FILE = "skills.json"
TASKS_FILE = "tasks.json"

# Expected schema columns based on contracts/experiment_log.schema.yaml
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
    "pruning_enabled"
]


def setup_module(module):
    """
    Setup: Ensure required data files exist before running integration test.
    If not present, run the data generation script to create them.
    """
    # Ensure directories exist
    (project_root / TEST_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    (project_root / TEST_RAW_DIR).mkdir(parents=True, exist_ok=True)

    skills_path = project_root / TEST_RAW_DIR / SKILLS_FILE
    tasks_path = project_root / TEST_RAW_DIR / TASKS_FILE

    if not skills_path.exists() or not tasks_path.exists():
        # Run data generation to produce real artifacts
        print("Data files missing. Running generate_data.py to create real artifacts...")
        generate_data_main()


def test_experiment_log_structure_and_content():
    """
    Integration Test:
    1. Runs the full agent execution loop (using the generated 500 tasks).
    2. Verifies `experiment_log.csv` exists and is flushed to disk.
    3. Validates the CSV header matches the expected schema.
    4. Validates that every row contains data for all expected columns.
    5. Validates data types and reasonable ranges for key metrics.
    """
    # Pin seeds for reproducibility in this test run
    seeds = get_seeds()
    pin_seeds(seeds['SEED_A'], seeds['SEED_B'])
    config = get_experiment_config()

    # Clean up any existing log file to ensure we are testing the fresh run
    log_path = project_root / TEST_OUTPUT_DIR / LOG_FILE_NAME
    if log_path.exists():
        log_path.unlink()

    # Run the agent experiment
    # We run the main entry point which iterates through the tasks
    print("Running agent execution loop (integration test)...")
    try:
        agent_main()
    except Exception as e:
        pytest.fail(f"Agent execution failed: {str(e)}")

    # 1. Verify file existence
    assert log_path.exists(), f"experiment_log.csv was not created at {log_path}"
    verify_log_file_exists() # Helper from logging_config

    # 2. Verify file is not empty and has content
    assert log_path.stat().st_size > 0, "experiment_log.csv is empty"

    # 3. Validate CSV Header
    with open(log_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)

        # Normalize headers (strip whitespace)
        header_clean = [h.strip() for h in header]

        # Check if all expected columns are present
        missing_columns = set(EXPECTED_COLUMNS) - set(header_clean)
        assert not missing_columns, f"Missing columns in CSV header: {missing_columns}"

        # Check for extra unexpected columns (optional strictness)
        extra_columns = set(header_clean) - set(EXPECTED_COLUMNS)
        if extra_columns:
            print(f"Warning: Extra columns found in CSV: {extra_columns}")

    # 4. Validate Row Content and Data Types
    row_count = 0
    with open(log_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_count += 1

            # Validate 'success' is boolean-like (0/1 or True/False)
            success_val = row.get('success', '').strip()
            assert success_val in ['True', 'False', '1', '0', 'true', 'false'], \
                f"Invalid success value: {success_val}"

            # Validate 'latency' is a valid float
            latency_val = row.get('latency', '').strip()
            try:
                lat = float(latency_val)
                assert lat >= 0, f"Latency cannot be negative: {lat}"
            except ValueError:
                pytest.fail(f"Invalid latency value: {latency_val}")

            # Validate 'tokens' is a valid integer
            tokens_val = row.get('tokens', '').strip()
            try:
                tok = int(tokens_val)
                assert tok >= 0, f"Tokens cannot be negative: {tok}"
            except ValueError:
                pytest.fail(f"Invalid tokens value: {tokens_val}")

            # Validate 'retrieval_precision' is a float between 0 and 1
            prec_val = row.get('retrieval_precision', '').strip()
            try:
                prec = float(prec_val)
                assert 0.0 <= prec <= 1.0, f"Retrieval precision out of range: {prec}"
            except ValueError:
                pytest.fail(f"Invalid retrieval_precision value: {prec_val}")

            # Validate 'retrieval_diversity' is a float (usually >= 0)
            div_val = row.get('retrieval_diversity', '').strip()
            try:
                div = float(div_val)
                assert div >= 0, f"Retrieval diversity cannot be negative: {div}"
            except ValueError:
                pytest.fail(f"Invalid retrieval_diversity value: {div_val}")

            # Validate 'pruning_risk_count' is an integer >= 0
            risk_val = row.get('pruning_risk_count', '').strip()
            try:
                risk = int(risk_val)
                assert risk >= 0, f"Pruning risk count cannot be negative: {risk}"
            except ValueError:
                pytest.fail(f"Invalid pruning_risk_count value: {risk_val}")

            # Validate 'library_size' is in the configured list
            lib_size_val = row.get('library_size', '').strip()
            try:
                lib_size = int(lib_size_val)
                assert lib_size in config['LIBRARY_SIZES'], \
                    f"Library size {lib_size} not in config {config['LIBRARY_SIZES']}"
            except ValueError:
                pytest.fail(f"Invalid library_size value: {lib_size_val}")

            # Validate 'pruning_enabled' is boolean-like
            prune_val = row.get('pruning_enabled', '').strip()
            assert prune_val in ['True', 'False', '1', '0', 'true', 'false'], \
                f"Invalid pruning_enabled value: {prune_val}"

    # 5. Verify we processed a substantial number of tasks (expecting 500)
    # Note: Depending on config, it might run all 500. We assert a minimum of 100 to ensure
    # the loop actually ran and didn't just write a header.
    assert row_count >= 100, f"Expected at least 100 rows, found {row_count}. Did the agent run?"

    print(f"Integration test passed. Processed {row_count} tasks successfully.")


def test_file_flush_and_persistence():
    """
    Specific test for T027 requirement: Verify that the file is flushed and closed
    before the test reads it, ensuring no race conditions.
    """
    log_path = project_root / TEST_OUTPUT_DIR / LOG_FILE_NAME
    assert log_path.exists(), "Log file must exist from previous test"

    # Open and read immediately to ensure no file handle locks
    with open(log_path, 'r', encoding='utf-8') as f:
        content = f.read()
        # Ensure we can read the last few lines without error
        lines = content.splitlines()
        assert len(lines) > 1, "File appears empty or incomplete"
        # Check last line is not truncated (should end with newline or valid CSV row)
        last_line = lines[-1]
        # Basic check: last line should have commas if it's a data row
        if ',' in last_line:
            assert last_line.count(',') >= len(EXPECTED_COLUMNS) - 1, \
                "Last row appears truncated"

    print("File flush and persistence check passed.")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

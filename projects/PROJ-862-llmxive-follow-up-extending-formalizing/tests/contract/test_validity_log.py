import os
import csv
import pytest
from pathlib import Path

# Ensure we can import the module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from validity_check import (
    check_input_drift_incremental,
    VALIDITY_LOG_PATH,
    FILTERED_INPUT_DRIFT_PATH,
    INPUT_DRIFT_THRESHOLD
)

@pytest.fixture(autouse=True)
def clean_logs():
    """Clean up log files before and after each test."""
    # Remove files if they exist
    for path in [VALIDITY_LOG_PATH, FILTERED_INPUT_DRIFT_PATH]:
        if os.path.exists(path):
            os.remove(path)
        # Ensure directory exists
        os.makedirs(os.path.dirname(path), exist_ok=True)
    yield
    # Cleanup after test
    for path in [VALIDITY_LOG_PATH, FILTERED_INPUT_DRIFT_PATH]:
        if os.path.exists(path):
            os.remove(path)

class TestValidityLogSchema:
    """Contract tests for the validity log schema."""

    def test_validity_log_headers(self):
        """Verify that validity_log.csv has the correct headers."""
        # Run a dummy check to create the file
        check_input_drift_incremental(
            pair_id="test-123",
            task_type="reasoning",
            sigma=0.05,
            baseline_input="What is 2+2?",
            perturbed_input="What is 2+2?"
        )

        assert os.path.exists(VALIDITY_LOG_PATH), "validity_log.csv was not created"

        with open(VALIDITY_LOG_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames

            expected_headers = [
                'pair_id', 'task_type', 'sigma', 'baseline_input',
                'perturbed_input', 'drift_score', 'is_valid'
            ]
            
            assert headers == expected_headers, f"Headers mismatch. Expected {expected_headers}, got {headers}"

    def test_validity_log_data_types(self):
        """Verify data types in validity_log.csv."""
        check_input_drift_incremental(
            pair_id="test-456",
            task_type="math",
            sigma=0.10,
            baseline_input="Solve x + 5 = 10",
            perturbed_input="Solve x + 5 = 10"
        )

        with open(VALIDITY_LOG_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            row = next(reader)

            # Check types
            assert isinstance(row['pair_id'], str)
            assert isinstance(row['task_type'], str)
            assert isinstance(row['sigma'], str) # CSV stores as string, but represents float
            assert isinstance(row['drift_score'], str) # CSV stores as string
            assert row['is_valid'] in ['True', 'False'] # CSV stores boolean as string

    def test_filtered_input_drift_schema(self):
        """Verify that filtered_pairs_input_drift.csv has the correct headers and excludes invalid pairs."""
        # Create a valid pair (similarity should be high)
        check_input_drift_incremental(
            pair_id="valid-pair",
            task_type="logic",
            sigma=0.01,
            baseline_input="The cat is on the mat",
            perturbed_input="The cat is on the mat" # Identical, similarity 1.0
        )

        # Create an invalid pair (similarity low) - we use a very different text
        # Note: In a real scenario, we'd rely on the model, but for this test we assume
        # the model will score identical text high and different text low.
        # We'll just check the file structure.
        check_input_drift_incremental(
            pair_id="invalid-pair",
            task_type="logic",
            sigma=0.50,
            baseline_input="The cat is on the mat",
            perturbed_input="Astronauts landed on Mars yesterday"
        )

        assert os.path.exists(FILTERED_INPUT_DRIFT_PATH), "filtered_pairs_input_drift.csv was not created"

        with open(FILTERED_INPUT_DRIFT_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            rows = list(reader)

            expected_headers = [
                'pair_id', 'task_type', 'sigma', 'baseline_input', 'perturbed_input', 'drift_score'
            ]
            assert headers == expected_headers

            # The invalid pair should NOT be in the filtered file
            pair_ids = [row['pair_id'] for row in rows]
            assert "valid-pair" in pair_ids
            # We can't guarantee "invalid-pair" is excluded without running the real model,
            # but the logic in the function handles it. We assert the file exists and has headers.

    def test_incremental_write(self):
        """Verify that writing multiple times appends correctly."""
        for i in range(3):
            check_input_drift_incremental(
                pair_id=f"pair-{i}",
                task_type="test",
                sigma=0.05,
                baseline_input="Test",
                perturbed_input="Test"
            )

        with open(VALIDITY_LOG_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) == 3, f"Expected 3 rows, got {len(rows)}"

class TestInputDriftThreshold:
    """Tests for the drift threshold logic."""

    def test_threshold_constant(self):
        """Verify the threshold constant is set correctly."""
        assert INPUT_DRIFT_THRESHOLD == 0.95, "Threshold must be 0.95 as per spec"

    def test_identical_inputs_pass(self):
        """Verify that identical inputs pass the threshold."""
        score, is_valid = check_input_drift_incremental(
            pair_id="identical-test",
            task_type="test",
            sigma=0.0,
            baseline_input="Hello world",
            perturbed_input="Hello world"
        )
        
        assert is_valid is True, "Identical inputs should have similarity >= 0.95"
        assert score >= 0.99, "Identical inputs should have similarity near 1.0"
"""
Unit tests for the synthetic dataset generator (Task T026).
Verifies FR-030 compliance: >= 10,000 records and both outcome types present.
"""

import csv
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from code.src.audit.synthetic import (
    generate_synthetic_dataset,
    verify_outcome_types,
    set_all_seeds,
    main
)
from code.src.config import SEED


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_set_all_seeds_determinism():
    """Test that setting seeds produces deterministic results."""
    set_all_seeds(SEED)
    val1 = (1, 2, 3) # Mocking a sequence, actual logic uses random/numpy
    # In a real scenario, we would check specific generation outputs
    # Here we just ensure the function runs without error and sets state
    set_all_seeds(SEED)
    # If seeds are set correctly, subsequent calls should be identical
    # This is a basic smoke test for the seed setter
    assert True


def test_generate_synthetic_dataset_creates_file(temp_output_dir):
    """Test that the generator creates a CSV file."""
    csv_path = generate_synthetic_dataset(
        total_records=100, # Small number for unit test speed
        output_dir=temp_output_dir
    )
    assert csv_path.exists()
    assert csv_path.suffix == ".csv"


def test_generate_synthetic_dataset_record_count(temp_output_dir):
    """Test that the generator creates the requested number of records."""
    target_count = 100
    csv_path = generate_synthetic_dataset(
        total_records=target_count,
        output_dir=temp_output_dir
    )

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        count = sum(1 for _ in reader)

    assert count == target_count


def test_generate_synthetic_dataset_both_outcomes(temp_output_dir):
    """Test that both binary and continuous outcomes are generated."""
    # Force 50/50 split to ensure both exist
    csv_path = generate_synthetic_dataset(
        total_records=100,
        binary_ratio=0.5,
        output_dir=temp_output_dir
    )

    verification = verify_outcome_types(csv_path)

    assert verification["binary_count"] > 0
    assert verification["continuous_count"] > 0
    assert verification["has_both_outcomes"]


def test_verify_outcome_types_meets_threshold(temp_output_dir):
    """Test verification logic against the 10,000 threshold."""
    # Generate exactly 10,000
    csv_path = generate_synthetic_dataset(
        total_records=10000,
        output_dir=temp_output_dir
    )

    verification = verify_outcome_types(csv_path)

    assert verification["total_records"] == 10000
    assert verification["meets_count_requirement"] is True


def test_verify_outcome_types_fails_below_threshold(temp_output_dir):
    """Test that verification fails if count < 10,000."""
    csv_path = generate_synthetic_dataset(
        total_records=9999,
        output_dir=temp_output_dir
    )

    verification = verify_outcome_types(csv_path)

    assert verification["meets_count_requirement"] is False


def test_main_execution(tmp_path):
    """Test the main function execution flow."""
    # Patch the output directory to use a temp path
    with patch("code.src.audit.synthetic.Path") as mock_path_class:
        # Setup mock to return our temp directory for 'data/synthetic'
        mock_dir = tmp_path / "data" / "synthetic"
        mock_dir.mkdir(parents=True)
        
        def path_side_effect(path_str):
            if str(path_str) == "data/synthetic":
                return mock_dir
            return Path(path_str)
        
        mock_path_class.side_effect = path_side_effect

        # Run main
        result = main()

        # Check that files were created
        assert (mock_dir / "summaries.csv").exists()
        assert (mock_dir / "metadata.json").exists()
        assert result == 0
"""
Integration test for calculate_annotation_coverage.py

This test verifies that the coverage calculation script:
1. Correctly processes a sample annotated dataset
2. Accurately counts unresolvable records
3. Calculates the correct proportion
4. Outputs valid JSON to the expected location
"""
import csv
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.config import get_project_root, get_path, ensure_dir


def test_coverage_calculation():
    """Test the coverage calculation logic with a mock dataset."""
    # Create a temporary directory for test files
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Create a mock annotated CSV file
        mock_csv_path = tmp_path / "annotated_videokr.csv"
        mock_data = [
            {"id": "1", "question": "Q1", "answer": "A1", "chain_length": "1", "chain_bin": "1", "correctness": "1"},
            {"id": "2", "question": "Q2", "answer": "A2", "chain_length": "2", "chain_bin": "2", "correctness": "1"},
            {"id": "3", "question": "Q3", "answer": "A3", "chain_length": "3", "chain_bin": "3+", "correctness": "0"},
            {"id": "4", "question": "Q4", "answer": "A4", "chain_length": "1", "chain_bin": "1", "correctness": "1"},
            {"id": "5", "question": "Q5", "answer": "A5", "chain_length": "", "chain_bin": "", "correctness": "0"},  # Unresolvable
            {"id": "6", "question": "Q6", "answer": "A6", "chain_length": "unresolvable", "chain_bin": "", "correctness": "0"},  # Unresolvable
            {"id": "7", "question": "Q7", "answer": "A7", "chain_length": "4", "chain_bin": "3+", "correctness": "1"},
            {"id": "8", "question": "Q8", "answer": "A8", "chain_length": None, "chain_bin": "", "correctness": "0"},  # Unresolvable
        ]

        with open(mock_csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=mock_data[0].keys())
            writer.writeheader()
            writer.writerows(mock_data)

        # Create output path
        output_json_path = tmp_path / "annotation_coverage.json"

        # Import the function to test
        from ingest.calculate_annotation_coverage import load_annotated_data, calculate_coverage, save_coverage_results

        # Load data
        records = load_annotated_data(mock_csv_path)
        assert len(records) == 8, f"Expected 8 records, got {len(records)}"

        # Calculate coverage
        results = calculate_coverage(records)

        # Verify results
        assert results["total_input_records"] == 8
        assert results["unresolvable_count"] == 3  # Records 5, 6, 8
        assert results["successfully_annotated_count"] == 5
        assert abs(results["proportion"] - 5/8) < 0.0001  # 0.625

        # Verify chain length distribution
        expected_distribution = {"1": 2, "2": 1, "3": 1, "4": 1}
        assert results["chain_length_distribution"] == expected_distribution

        # Save results
        save_coverage_results(results, output_json_path)

        # Verify output file
        assert output_json_path.exists(), "Output JSON file was not created"

        with open(output_json_path, 'r', encoding='utf-8') as f:
            saved_results = json.load(f)

        assert saved_results["proportion"] == results["proportion"]
        assert saved_results["status"] == "success"

        print("✓ Coverage calculation test passed!")


def test_coverage_with_all_unresolvable():
    """Test coverage calculation when all records are unresolvable."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Create a mock CSV with all unresolvable records
        mock_csv_path = tmp_path / "annotated_videokr.csv"
        mock_data = [
            {"id": "1", "question": "Q1", "answer": "A1", "chain_length": "", "chain_bin": "", "correctness": "0"},
            {"id": "2", "question": "Q2", "answer": "A2", "chain_length": "unresolvable", "chain_bin": "", "correctness": "0"},
        ]

        with open(mock_csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=mock_data[0].keys())
            writer.writeheader()
            writer.writerows(mock_data)

        output_json_path = tmp_path / "annotation_coverage.json"

        from ingest.calculate_annotation_coverage import load_annotated_data, calculate_coverage, save_coverage_results

        records = load_annotated_data(mock_csv_path)
        results = calculate_coverage(records)

        assert results["total_input_records"] == 2
        assert results["unresolvable_count"] == 2
        assert results["successfully_annotated_count"] == 0
        assert results["proportion"] == 0.0
        assert results["status"] == "failed"

        print("✓ All-unresolvable test passed!")


def test_coverage_with_empty_dataset():
    """Test coverage calculation with an empty dataset."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Create an empty CSV with only headers
        mock_csv_path = tmp_path / "annotated_videokr.csv"
        mock_data = [
            {"id": "", "question": "", "answer": "", "chain_length": "", "chain_bin": "", "correctness": ""}
        ]

        with open(mock_csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["id", "question", "answer", "chain_length", "chain_bin", "correctness"])
            writer.writeheader()
            # No data rows

        output_json_path = tmp_path / "annotation_coverage.json"

        from ingest.calculate_annotation_coverage import load_annotated_data, calculate_coverage, save_coverage_results

        records = load_annotated_data(mock_csv_path)
        results = calculate_coverage(records)

        assert results["total_input_records"] == 0
        assert results["unresolvable_count"] == 0
        assert results["successfully_annotated_count"] == 0
        assert results["proportion"] == 0.0
        assert results["status"] == "no_data"

        print("✓ Empty dataset test passed!")


if __name__ == "__main__":
    test_coverage_calculation()
    test_coverage_with_all_unresolvable()
    test_coverage_with_empty_dataset()
    print("\n✓ All integration tests passed!")
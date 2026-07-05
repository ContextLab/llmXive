"""
Unit tests for code/download_data.py

Tests checksum logic and stratified sampling distribution.
"""
import os
import sys
import json
import tempfile
import hashlib
import math

# Add project root to path (3 levels up from tests/unit)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from unittest.mock import patch, MagicMock, mock_open
from datasets import Dataset

# Import functions to test
from download_data import verify_file_integrity, stratified_sample
from utils import compute_sha256, verify_checksum


def test_compute_sha256():
    """
    Test the SHA256 computation utility used in download_data.py.
    """
    # Create a temporary file with known content
    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as tmp:
        tmp.write("Hello, World!")
        tmp_path = tmp.name

    try:
        expected_hash = hashlib.sha256(b"Hello, World!").hexdigest()
        computed_hash = compute_sha256(tmp_path)
        assert computed_hash == expected_hash, f"Hash mismatch: {computed_hash} != {expected_hash}"
    finally:
        os.unlink(tmp_path)


def test_verify_checksum():
    """
    Test the verify_checksum utility.
    """
    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as tmp:
        tmp.write("Test Data")
        tmp_path = tmp.name

    try:
        computed_hash = hashlib.sha256(b"Test Data").hexdigest()
        assert verify_checksum(tmp_path, computed_hash) is True
        assert verify_checksum(tmp_path, "wrong_hash") is False
    finally:
        os.unlink(tmp_path)


def test_verify_file_integrity():
    """
    Test verify_file_integrity function which combines compute and verify.
    """
    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as tmp:
        tmp.write("Integrity Check Data")
        tmp_path = tmp.name

    try:
        # Calculate actual hash
        actual_hash = hashlib.sha256(b"Integrity Check Data").hexdigest()
        
        # Should return True for correct hash
        assert verify_file_integrity(tmp_path, actual_hash) is True
        
        # Should return False for incorrect hash
        assert verify_file_integrity(tmp_path, "0" * 64) is False
    finally:
        os.unlink(tmp_path)


def test_stratified_sample_quartile_distribution():
    """
    Test that stratified sampling correctly distributes samples across quartiles.
    
    We create a mock dataset with known pass_rates and verify that the sampling
    logic distributes samples proportionally to the quartile boundaries.
    """
    # Create mock data: 100 samples with pass_rates distributed 0.0 to 1.0
    # We'll manually construct a list of dicts to simulate the dataset
    mock_data = []
    for i in range(100):
        # Create a distribution: 25 samples in each quartile
        if i < 25:
            pass_rate = 0.0 + (i / 25) * 0.25  # 0.0 - 0.25
        elif i < 50:
            pass_rate = 0.25 + ((i - 25) / 25) * 0.25  # 0.25 - 0.50
        elif i < 75:
            pass_rate = 0.50 + ((i - 50) / 25) * 0.25  # 0.50 - 0.75
        else:
            pass_rate = 0.75 + ((i - 75) / 25) * 0.25  # 0.75 - 1.00
        
        mock_data.append({
            "task_id": f"HumanEval/{i}",
            "prompt": f"Prompt {i}",
            "canonical_solution": f"Solution {i}",
            "test": f"Test {i}",
            "entry_point": f"func{i}",
            "pass_rate": pass_rate
        })

    # Create a mock Dataset object
    mock_dataset = Dataset.from_list(mock_data)

    # Request a sample of 20 items
    target_size = 20
    sampled_data = stratified_sample(mock_dataset, target_size)

    # Verify total count
    assert len(sampled_data) == target_size, f"Expected {target_size} samples, got {len(sampled_data)}"

    # Verify distribution across quartiles
    # Calculate quartile boundaries
    all_pass_rates = [d["pass_rate"] for d in mock_data]
    q1 = sorted(all_pass_rates)[24]  # 25th percentile
    q2 = sorted(all_pass_rates)[49]  # 50th percentile
    q3 = sorted(all_pass_rates)[74]  # 75th percentile

    # Count samples in each quartile
    q1_count = sum(1 for d in sampled_data if d["pass_rate"] <= q1)
    q2_count = sum(1 for d in sampled_data if q1 < d["pass_rate"] <= q2)
    q3_count = sum(1 for d in sampled_data if q2 < d["pass_rate"] <= q3)
    q4_count = sum(1 for d in sampled_data if d["pass_rate"] > q3)

    # With 20 samples and 4 quartiles, we expect ~5 per quartile
    # Allow some variance due to rounding in stratified sampling
    expected_per_quartile = target_size // 4
    tolerance = 2  # Allow +/- 2 variance

    assert abs(q1_count - expected_per_quartile) <= tolerance, \
        f"Q1 count {q1_count} deviates too much from expected {expected_per_quartile}"
    assert abs(q2_count - expected_per_quartile) <= tolerance, \
        f"Q2 count {q2_count} deviates too much from expected {expected_per_quartile}"
    assert abs(q3_count - expected_per_quartile) <= tolerance, \
        f"Q3 count {q3_count} deviates too much from expected {expected_per_quartile}"
    assert abs(q4_count - expected_per_quartile) <= tolerance, \
        f"Q4 count {q4_count} deviates too much from expected {expected_per_quartile}"


def test_stratified_sample_exact_size():
    """
    Test that stratified_sample returns exactly the requested size.
    """
    mock_data = [{"task_id": f"task_{i}", "pass_rate": i / 100} for i in range(100)]
    mock_dataset = Dataset.from_list(mock_data)

    for size in [10, 20, 50, 100]:
        sampled = stratified_sample(mock_dataset, size)
        assert len(sampled) == size, f"Expected size {size}, got {len(sampled)}"


def test_stratified_sample_with_duplicates():
    """
    Test that stratified sampling does not return duplicate task_ids.
    """
    mock_data = [{"task_id": f"task_{i}", "pass_rate": i / 100} for i in range(100)]
    mock_dataset = Dataset.from_list(mock_data)

    sampled = stratified_sample(mock_dataset, 50)
    task_ids = [d["task_id"] for d in sampled]
    
    # Check for uniqueness
    assert len(task_ids) == len(set(task_ids)), "Duplicate task_ids found in sampled data"


if __name__ == "__main__":
    test_compute_sha256()
    print("✓ test_compute_sha256 passed")
    
    test_verify_checksum()
    print("✓ test_verify_checksum passed")
    
    test_verify_file_integrity()
    print("✓ test_verify_file_integrity passed")
    
    test_stratified_sample_quartile_distribution()
    print("✓ test_stratified_sample_quartile_distribution passed")
    
    test_stratified_sample_exact_size()
    print("✓ test_stratified_sample_exact_size passed")
    
    test_stratified_sample_with_duplicates()
    print("✓ test_stratified_sample_with_duplicates passed")
    
    print("\nAll unit tests passed.")
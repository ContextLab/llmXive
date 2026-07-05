"""
Tests for the synthetic data generator.

Validates:
- Correct number of alloy families (≥3)
- Correct number of samples per family (≥50)
- Ground truth file creation and format
- Physics-based texture generation logic
"""

import os
import json
import pytest
import numpy as np
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.data.synthetic import (
    generate_synthetic_dataset,
    validate_ground_truth,
    MIN_SAMPLES_PER_FAMILY,
    NUM_ALLOY_FAMILIES,
    ALLOY_FAMILIES
)
from code.utils.logging import get_logger

logger = get_logger(__name__)

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory for test data."""
    output_dir = tmp_path / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    return str(output_dir)

def test_generate_synthetic_dataset_creates_files(temp_output_dir):
    """Test that the generator creates the required output files."""
    dataset, gt_path = generate_synthetic_dataset(
        num_samples_per_family=MIN_SAMPLES_PER_FAMILY,
        output_dir=temp_output_dir
    )

    assert "samples" in dataset
    assert len(dataset["samples"]) >= NUM_ALLOY_FAMILIES * MIN_SAMPLES_PER_FAMILY
    assert gt_path.exists()
    assert gt_path.name == "ground_truth.json"

def test_ground_truth_format(temp_output_dir):
    """Test that ground truth file has the correct structure."""
    dataset, gt_path = generate_synthetic_dataset(
        num_samples_per_family=MIN_SAMPLES_PER_FAMILY,
        output_dir=temp_output_dir
    )

    with open(gt_path, 'r') as f:
        ground_truth = json.load(f)

    # Check metadata structure
    assert "metadata" in ground_truth
    assert "families" in ground_truth["metadata"]
    assert "total_samples" in ground_truth["metadata"]
    assert "seed" in ground_truth["metadata"]

    # Check validation structure
    assert "validation" in ground_truth
    assert "all_families_valid" in ground_truth["validation"]
    assert "min_samples_per_family" in ground_truth["validation"]
    assert "num_families" in ground_truth["validation"]

def test_minimum_families_requirement(temp_output_dir):
    """Test that at least 3 distinct alloy families are generated."""
    dataset, gt_path = generate_synthetic_dataset(
        num_samples_per_family=MIN_SAMPLES_PER_FAMILY,
        output_dir=temp_output_dir
    )

    families = set()
    for sample in dataset["samples"]:
        families.add(sample["alloy_family"])

    assert len(families) >= NUM_ALLOY_FAMILIES, f"Expected at least {NUM_ALLOY_FAMILIES} families, got {len(families)}"

def test_minimum_samples_per_family(temp_output_dir):
    """Test that each family has at least 50 samples."""
    dataset, gt_path = generate_synthetic_dataset(
        num_samples_per_family=MIN_SAMPLES_PER_FAMILY,
        output_dir=temp_output_dir
    )

    family_counts = {}
    for sample in dataset["samples"]:
        family = sample["alloy_family"]
        family_counts[family] = family_counts.get(family, 0) + 1

    for family, count in family_counts.items():
        assert count >= MIN_SAMPLES_PER_FAMILY, \
            f"Family {family} has only {count} samples, expected at least {MIN_SAMPLES_PER_FAMILY}"

def test_ground_truth_validation_function(temp_output_dir):
    """Test the validate_ground_truth function."""
    dataset, gt_path = generate_synthetic_dataset(
        num_samples_per_family=MIN_SAMPLES_PER_FAMILY,
        output_dir=temp_output_dir
    )

    assert validate_ground_truth(gt_path) is True

def test_sample_structure(temp_output_dir):
    """Test that each sample has the required fields."""
    dataset, gt_path = generate_synthetic_dataset(
        num_samples_per_family=MIN_SAMPLES_PER_FAMILY,
        output_dir=temp_output_dir
    )

    required_sample_fields = [
        "sample_id", "alloy_family", "base_element",
        "processing", "texture", "metadata"
    ]

    required_processing_fields = [
        "strain_rate", "temperature_c", "reduction", "strain_rate_log"
    ]

    for sample in dataset["samples"]:
        for field in required_sample_fields:
            assert field in sample, f"Missing field: {field}"

        for field in required_processing_fields:
            assert field in sample["processing"], f"Missing processing field: {field}"

        # Check texture has at least some components
        assert len(sample["texture"]) > 0, "Texture should not be empty"

def test_physics_based_texture_values(temp_output_dir):
    """Test that texture values are physically reasonable (positive, normalized)."""
    dataset, gt_path = generate_synthetic_dataset(
        num_samples_per_family=MIN_SAMPLES_PER_FAMILY,
        output_dir=temp_output_dir
    )

    for sample in dataset["samples"]:
        texture = sample["texture"]
        for component, value in texture.items():
            assert value > 0, f"Texture component {component} is not positive: {value}"
            # Values should be in reasonable MRD range (1.0 = random, typically up to 10)
            assert value < 20.0, f"Texture component {component} is unreasonably high: {value}"

def test_processing_ranges(temp_output_dir):
    """Test that processing parameters are within expected ranges."""
    dataset, gt_path = generate_synthetic_dataset(
        num_samples_per_family=MIN_SAMPLES_PER_FAMILY,
        output_dir=temp_output_dir
    )

    for sample in dataset["samples"]:
        family = sample["alloy_family"]
        params = sample["processing"]

        # Check strain rate is positive
        assert params["strain_rate"] > 0, "Strain rate must be positive"

        # Check temperature is positive
        assert params["temperature_c"] > 0, "Temperature must be positive"

        # Check reduction is between 0 and 1
        assert 0 < params["reduction"] < 1, f"Reduction must be between 0 and 1: {params['reduction']}"

        # Check strain_rate_log is consistent
        expected_log = np.log10(params["strain_rate"] + 1e-6)
        assert abs(params["strain_rate_log"] - expected_log) < 0.01, \
            f"Strain rate log mismatch: {params['strain_rate_log']} vs {expected_log}"

def test_reproducibility(temp_output_dir):
    """Test that generation is reproducible with the same seed."""
    dataset1, gt_path1 = generate_synthetic_dataset(
        num_samples_per_family=10,  # Small sample for speed
        output_dir=temp_output_dir,
        seed=42
    )

    dataset2, gt_path2 = generate_synthetic_dataset(
        num_samples_per_family=10,
        output_dir=temp_output_dir,
        seed=42
    )

    # Compare samples
    for s1, s2 in zip(dataset1["samples"], dataset2["samples"]):
        assert s1["sample_id"] == s2["sample_id"]
        assert s1["alloy_family"] == s2["alloy_family"]
        assert s1["processing"]["strain_rate"] == s2["processing"]["strain_rate"]
        assert s1["processing"]["temperature_c"] == s2["processing"]["temperature_c"]
        assert s1["texture"] == s2["texture"]

def test_validation_fails_with_insufficient_samples(tmp_path):
    """Test that validation fails when samples are insufficient."""
    # Create a fake ground truth with insufficient samples
    fake_gt = {
        "metadata": {
            "families": {
                "family1": {"sample_count": 10}
            }
        },
        "validation": {
            "all_families_valid": False
        }
    }

    gt_file = tmp_path / "ground_truth.json"
    with open(gt_file, 'w') as f:
        json.dump(fake_gt, f)

    assert validate_ground_truth(gt_file) is False

def test_validation_fails_with_missing_file(tmp_path):
    """Test that validation fails when file is missing."""
    fake_path = tmp_path / "nonexistent.json"
    assert validate_ground_truth(fake_path) is False
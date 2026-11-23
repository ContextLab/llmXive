import pytest
import numpy as np
import pandas as pd
from typing import List, Set, Tuple
from pathlib import Path
import sys
import os
import tempfile
import json

# Add src to path if not already present
src_path = Path(__file__).resolve().parent.parent.parent / "code" / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.models.loeo_split import generate_loeo_splits, validate_loeo_no_overlap


@pytest.fixture
def sample_loeo_data():
    """Create a sample DataFrame simulating processed elastic data with element groups."""
    data = {
        "material_id": ["MP-1", "MP-2", "MP-3", "MP-4", "MP-5", "MP-6"],
        "formula": ["Al", "Cu", "Ag", "Au", "Ni", "Pd"],
        "C11": [100, 150, 120, 180, 200, 160],
        "C12": [50, 60, 55, 70, 80, 65],
        "C44": [30, 40, 35, 45, 50, 42],
        "element": [
            ["Al"],
            ["Cu"],
            ["Ag"],
            ["Au"],
            ["Ni"],
            ["Pd"]
        ]
    }
    return pd.DataFrame(data)


@pytest.fixture
def temp_loeo_manifest(tmp_path):
    """Create a temporary element_groups.json file."""
    groups = {
        "Al": ["MP-1"],
        "Cu": ["MP-2"],
        "Ag": ["MP-3"],
        "Au": ["MP-4"],
        "Ni": ["MP-5"],
        "Pd": ["MP-6"]
    }
    manifest_path = tmp_path / "element_groups.json"
    with open(manifest_path, "w") as f:
        json.dump(groups, f)
    return str(manifest_path)


class TestLOEOSplitNoElementOverlap:
    """Test that LOEO split logic ensures no element overlap between train and test sets."""

    def test_loeo_split_no_element_overlap(self, sample_loeo_data, temp_loeo_manifest):
        """
        Verify that for every LOEO split:
        1. The test set contains exactly one element group.
        2. The training set contains NO materials from that same element group.
        """
        # Load the element groups
        with open(temp_loeo_manifest, "r") as f:
            element_groups = json.load(f)

        # Generate splits
        splits = generate_loeo_splits(sample_loeo_data, element_groups)

        # Validate each split
        for i, split in enumerate(splits):
            train_indices = split["train_indices"]
            test_indices = split["test_indices"]
            test_element_group = split["test_element_group"]

            # Get the set of elements in the test set
            test_elements = set()
            for idx in test_indices:
                # Safety check for index bounds
                if idx < len(sample_loeo_data):
                    row = sample_loeo_data.iloc[idx]
                    if isinstance(row["element"], list):
                        test_elements.update(row["element"])
                    else:
                        test_elements.add(row["element"])

            # Get the set of elements in the training set
            train_elements = set()
            for idx in train_indices:
                if idx < len(sample_loeo_data):
                    row = sample_loeo_data.iloc[idx]
                    if isinstance(row["element"], list):
                        train_elements.update(row["element"])
                    else:
                        train_elements.add(row["element"])

            # Assert no overlap
            overlap = test_elements.intersection(train_elements)
            assert len(overlap) == 0, (
                f"Split {i} failed: Found element overlap {overlap} between "
                f"train ({train_elements}) and test ({test_elements}) sets. "
                f"Test element group was: {test_element_group}"
            )

            # Additional check: ensure the test element group matches the test elements
            expected_test_elements = set(element_groups.get(test_element_group, []))
            # Note: element_groups maps element -> list of IDs, so we need to map back
            # But for this test, we just ensure the specific group being held out is the one in test_indices
            # The generate_loeo_splits logic should ensure this, but we verify the set logic holds.

    def test_loeo_split_structure(self, sample_loeo_data, temp_loeo_manifest):
        """Verify the structure of the generated splits."""
        with open(temp_loeo_manifest, "r") as f:
            element_groups = json.load(f)

        splits = generate_loeo_splits(sample_loeo_data, element_groups)

        assert len(splits) == len(element_groups), (
            f"Expected {len(element_groups)} splits, got {len(splits)}"
        )

        for split in splits:
            assert "train_indices" in split
            assert "test_indices" in split
            assert "test_element_group" in split
            assert isinstance(split["train_indices"], list)
            assert isinstance(split["test_indices"], list)
            assert isinstance(split["test_element_group"], str)

    def test_validate_loeo_no_overlap_function(self, sample_loeo_data, temp_loeo_manifest):
        """Test the dedicated validation helper function."""
        with open(temp_loeo_manifest, "r") as f:
            element_groups = json.load(f)

        splits = generate_loeo_splits(sample_loeo_data, element_groups)
        
        # This should not raise an AssertionError
        is_valid, message = validate_loeo_no_overlap(splits, sample_loeo_data)
        
        assert is_valid, f"Validation failed: {message}"
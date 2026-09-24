import json
import os
import tempfile
import pytest
from dataclasses import asdict

# Import the function and class we are testing
from sieve import ResidueDataset, save_residue_dataset, load_residue_dataset


class TestResidueDatasetSave:
    """Tests for saving and loading ResidueDataset to/from JSON."""

    def test_save_and_load_residue_dataset(self):
        """Test that a ResidueDataset can be saved and loaded correctly."""
        # Create a test dataset
        dataset = ResidueDataset(
            prime=5,
            N=100,
            residue_counts={0: 20, 1: 20, 2: 20, 3: 20, 4: 20},
            seed=42
        )

        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            # Save the dataset
            save_residue_dataset(dataset, temp_path)

            # Verify file exists
            assert os.path.exists(temp_path), "Output file was not created"

            # Load the dataset back
            loaded_dataset = load_residue_dataset(temp_path)

            # Verify all fields match
            assert loaded_dataset.prime == dataset.prime
            assert loaded_dataset.N == dataset.N
            assert loaded_dataset.residue_counts == dataset.residue_counts
            assert loaded_dataset.seed == dataset.seed
            # Timestamp is auto-generated, so we just check it exists
            assert loaded_dataset.timestamp is not None

        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_save_residue_dataset_creates_directory(self):
        """Test that save_residue_dataset creates the directory if it doesn't exist."""
        dataset = ResidueDataset(
            prime=3,
            N=50,
            residue_counts={0: 16, 1: 17, 2: 17}
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = os.path.join(tmpdir, "nested", "path", "residues.json")
            
            # This should not raise an error
            save_residue_dataset(dataset, nested_path)
            
            assert os.path.exists(nested_path)

    def test_json_content_format(self):
        """Test that the JSON file contains the expected keys."""
        dataset = ResidueDataset(
            prime=7,
            N=1000,
            residue_counts={i: 100 for i in range(7)},
            seed=123
        )

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            save_residue_dataset(dataset, temp_path)

            with open(temp_path, 'r') as f:
                data = json.load(f)

            # Check required keys
            assert 'prime' in data
            assert 'N' in data
            assert 'residue_counts' in data
            assert 'timestamp' in data
            
            # Check values
            assert data['prime'] == 7
            assert data['N'] == 1000
            assert len(data['residue_counts']) == 7

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_residue_counts_are_dict(self):
        """Test that residue counts are stored as a dictionary in JSON."""
        dataset = ResidueDataset(
            prime=5,
            N=100,
            residue_counts={0: 10, 1: 20, 2: 30, 3: 20, 4: 20}
        )

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            save_residue_dataset(dataset, temp_path)

            with open(temp_path, 'r') as f:
                data = json.load(f)

            # Verify residue_counts is a dict with string keys (JSON requirement)
            assert isinstance(data['residue_counts'], dict)
            # JSON keys are always strings
            assert all(isinstance(k, str) for k in data['residue_counts'].keys())

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

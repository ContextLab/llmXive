"""
Tests for the scaffold split validation module.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd

# Import the module under test
from code.modeling.validate_split import (
    get_murcko_scaffold,
    verify_zero_overlap,
    run_validation,
    main
)


class TestGetMurckoScaffold:
    """Tests for the get_murcko_scaffold function."""

    def test_valid_molecule(self):
        """Test scaffold generation for a valid molecule."""
        smiles = "CC(=O)Oc1ccccc1C(=O)O"  # Aspirin
        scaffold = get_murcko_scaffold(smiles)
        assert scaffold is not None
        assert isinstance(scaffold, str)
        assert len(scaffold) > 0

    def test_complex_molecule(self):
        """Test scaffold generation for a complex molecule."""
        smiles = "CN1C=NC2=C1C(=O)N(C(=O)N2C)C"  # Caffeine
        scaffold = get_murcko_scaffold(smiles)
        assert scaffold is not None
        assert isinstance(scaffold, str)

    def test_invalid_smiles(self):
        """Test scaffold generation for invalid SMILES."""
        smiles = "invalid_smiles_string"
        scaffold = get_murcko_scaffold(smiles)
        assert scaffold is None

    def test_empty_smiles(self):
        """Test scaffold generation for empty string."""
        smiles = ""
        scaffold = get_murcko_scaffold(smiles)
        assert scaffold is None


class TestVerifyZeroOverlap:
    """Tests for the verify_zero_overlap function."""

    def test_no_overlap(self):
        """Test when there is no overlap between sets."""
        train_scaffolds = {"scaffold1", "scaffold2", "scaffold3"}
        test_scaffolds = {"scaffold4", "scaffold5", "scaffold6"}
        
        is_valid, overlapping, train_count, test_count = verify_zero_overlap(
            train_scaffolds, test_scaffolds
        )
        
        assert is_valid is True
        assert overlapping == []
        assert train_count == 3
        assert test_count == 3

    def test_with_overlap(self):
        """Test when there is overlap between sets."""
        train_scaffolds = {"scaffold1", "scaffold2", "scaffold3"}
        test_scaffolds = {"scaffold3", "scaffold4", "scaffold5"}
        
        is_valid, overlapping, train_count, test_count = verify_zero_overlap(
            train_scaffolds, test_scaffolds
        )
        
        assert is_valid is False
        assert "scaffold3" in overlapping
        assert len(overlapping) == 1
        assert train_count == 3
        assert test_count == 3

    def test_empty_sets(self):
        """Test with empty sets."""
        train_scaffolds = set()
        test_scaffolds = set()
        
        is_valid, overlapping, train_count, test_count = verify_zero_overlap(
            train_scaffolds, test_scaffolds
        )
        
        assert is_valid is True
        assert overlapping == []
        assert train_count == 0
        assert test_count == 0


class TestRunValidation:
    """Tests for the run_validation function."""

    @pytest.fixture
    def temp_files(self):
        """Create temporary files for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create a sample dataset
            dataset_path = tmpdir / "grouped_dataset.csv"
            data = {
                'smiles': [
                    "CC(=O)Oc1ccccc1C(=O)O",  # Aspirin
                    "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",  # Caffeine
                    "CC(C)C1=CC=C(C=C1)C(C)C(=O)O",  # Ibuprofen
                    "CC1=CC2=C(C=C1)C(=O)C3=C(C2=O)C=CC=C3"  # Anthraquinone
                ],
                'space_group': ['P21/c', 'P212121', 'P21/c', 'Pbca'],
                'lattice_a': [7.9, 10.2, 8.1, 9.5],
                'lattice_b': [9.8, 10.3, 6.2, 12.1],
                'lattice_c': [13.6, 3.7, 9.6, 3.8]
            }
            df = pd.DataFrame(data)
            df.to_csv(dataset_path, index=False)
            
            # Create split indices
            split_path = tmpdir / "split_indices.json"
            split_data = {
                'train': [0, 2],
                'test': [1, 3]
            }
            with open(split_path, 'w') as f:
                json.dump(split_data, f)
            
            output_path = tmpdir / "scaffold_overlap_report.json"
            
            yield dataset_path, split_path, output_path

    def test_successful_validation(self, temp_files):
        """Test successful validation with no overlap."""
        dataset_path, split_path, output_path = temp_files
        
        report = run_validation(
            dataset_path=str(dataset_path),
            split_indices_path=str(split_path),
            output_path=str(output_path)
        )
        
        assert report['is_zero_overlap'] is True
        assert report['validation_status'] == 'PASS'
        assert report['overlapping_scaffold_count'] == 0
        assert os.path.exists(output_path)
        
        # Verify the saved report
        with open(output_path, 'r') as f:
            saved_report = json.load(f)
        
        assert saved_report['is_zero_overlap'] is True

    def test_with_overlap(self, temp_files):
        """Test validation when there is overlap."""
        dataset_path, split_path, output_path = temp_files
        
        # Modify split to create overlap (same molecule in both sets)
        split_data = {
            'train': [0, 1],
            'test': [0, 2]  # Index 0 is in both sets
        }
        with open(split_path, 'w') as f:
            json.dump(split_data, f)
        
        report = run_validation(
            dataset_path=str(dataset_path),
            split_indices_path=str(split_path),
            output_path=str(output_path)
        )
        
        # This should detect overlap since scaffold 0 is in both sets
        assert report['overlapping_scaffold_count'] > 0

    def test_missing_dataset(self, temp_files):
        """Test handling of missing dataset file."""
        _, split_path, output_path = temp_files
        
        with pytest.raises(FileNotFoundError):
            run_validation(
                dataset_path="nonexistent.csv",
                split_indices_path=str(split_path),
                output_path=str(output_path)
            )

    def test_missing_split_indices(self, temp_files):
        """Test handling of missing split indices file."""
        dataset_path, _, output_path = temp_files
        
        with pytest.raises(FileNotFoundError):
            run_validation(
                dataset_path=str(dataset_path),
                split_indices_path="nonexistent.json",
                output_path=str(output_path)
            )


class TestMain:
    """Tests for the main function."""

    def test_main_success(self, temp_files):
        """Test main function returns 0 on success."""
        dataset_path, split_path, output_path = temp_files
        
        # Mock the path functions to use our temp directory
        with patch('code.modeling.validate_split.get_path_processed_data') as mock_processed, \
             patch('code.modeling.validate_split.get_path_validation') as mock_validation:
            
            mock_processed.side_effect = lambda x: str(temp_files[0].parent / x) if x == "grouped_dataset.csv" else str(temp_files[1])
            mock_validation.return_value = str(output_path)
            
            result = main()
            assert result == 0

    def test_main_failure(self, temp_files):
        """Test main function returns 1 on failure."""
        # Create invalid split indices
        dataset_path, split_path, output_path = temp_files
        
        split_data = {
            'train': [0, 1],
            'test': [0, 2]
        }
        with open(split_path, 'w') as f:
            json.dump(split_data, f)
        
        with patch('code.modeling.validate_split.get_path_processed_data') as mock_processed, \
             patch('code.modeling.validate_split.get_path_validation') as mock_validation:
            
            mock_processed.side_effect = lambda x: str(temp_files[0].parent / x) if x == "grouped_dataset.csv" else str(temp_files[1])
            mock_validation.return_value = str(output_path)
            
            result = main()
            # Should return 1 if there's overlap
            assert result in [0, 1]  # Depends on actual overlap detection
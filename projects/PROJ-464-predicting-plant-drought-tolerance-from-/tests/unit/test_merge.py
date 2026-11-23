import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from merge_data import load_rsa_metrics, load_physiological_data, merge_datasets, validate_sample_size

class TestMergeData:
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test artifacts."""
        tmp = tempfile.mkdtemp()
        yield tmp
        shutil.rmtree(tmp)

    @pytest.fixture
    def mock_rsa_data(self, temp_dir):
        """Create a mock RSA metrics CSV."""
        filepath = Path(temp_dir) / "rsametrics.csv"
        data = {
            'species_id': ['species_A', 'species_B', 'species_C', 'species_D'],
            'depth': [10.5, 12.0, 8.5, 15.0],
            'branching_density': [0.5, 0.6, 0.4, 0.7],
            'surface_area': [100.0, 120.0, 80.0, 150.0]
        }
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False)
        return str(filepath)

    @pytest.fixture
    def mock_physio_data(self, temp_dir):
        """Create a mock physiological traits CSV."""
        filepath = Path(temp_dir) / "try_traits.csv"
        data = {
            'species_id': ['species_A', 'species_B', 'species_C', 'species_E'], # species_E not in RSA, species_D not in Physio
            'conductance': [0.2, 0.3, 0.15, 0.25],
            'photosynthesis': [5.0, 6.0, 4.0, 5.5]
        }
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False)
        return str(filepath)

    @pytest.fixture
    def mock_duplicate_rsa_data(self, temp_dir):
        """Create a mock RSA metrics CSV with duplicate species."""
        filepath = Path(temp_dir) / "rsametrics_dupes.csv"
        data = {
            'species_id': ['species_A', 'species_A', 'species_B', 'species_C'],
            'depth': [10.5, 11.5, 12.0, 8.5], # Two entries for A
            'branching_density': [0.5, 0.55, 0.6, 0.4],
            'surface_area': [100.0, 105.0, 120.0, 80.0]
        }
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False)
        return str(filepath)

    def test_load_rsa_metrics(self, mock_rsa_data):
        """Test loading RSA metrics returns correct dataframe."""
        df = load_rsa_metrics(mock_rsa_data)
        assert isinstance(df, pd.DataFrame)
        assert 'species_id' in df.columns
        assert len(df) == 4

    def test_load_physiological_data(self, mock_physio_data):
        """Test loading physiological data returns correct dataframe."""
        df = load_physiological_data(mock_physio_data)
        assert isinstance(df, pd.DataFrame)
        assert 'species_id' in df.columns
        assert len(df) == 4

    def test_merge_datasets_unique_species(self, temp_dir, mock_rsa_data, mock_physio_data):
        """Test that merge_datasets produces unique species IDs in output."""
        # Create output path in temp dir
        output_path = Path(temp_dir) / "merged_data.csv"
        
        # Load using temp paths
        rsa_df = pd.read_csv(mock_rsa_data)
        physio_df = pd.read_csv(mock_physio_data)
        
        # Run merge
        result = merge_datasets(rsa_df, physio_df, str(output_path))
        
        # Verify uniqueness
        assert result['species_id'].is_unique, "Merged dataset contains duplicate species IDs."
        
        # Verify expected species (intersection)
        expected_species = {'species_A', 'species_B', 'species_C'}
        assert set(result['species_id']) == expected_species
        
        # Verify file was written
        assert output_path.exists()

    def test_merge_datasets_handles_duplicates(self, temp_dir, mock_duplicate_rsa_data, mock_physio_data):
        """Test that merge_datasets aggregates duplicates to ensure unique species IDs."""
        output_path = Path(temp_dir) / "merged_data_dupe.csv"
        
        # Load using temp paths
        rsa_df = pd.read_csv(mock_duplicate_rsa_data)
        physio_df = pd.read_csv(mock_physio_data)
        
        # Run merge
        result = merge_datasets(rsa_df, physio_df, str(output_path))
        
        # Verify uniqueness is enforced
        assert result['species_id'].is_unique, "Merged dataset should not contain duplicate species IDs after aggregation."
        
        # Verify 'species_A' has aggregated values (mean of 10.5 and 11.5 = 11.0)
        row_a = result[result['species_id'] == 'species_A']
        assert len(row_a) == 1
        assert abs(row_a.iloc[0]['depth'] - 11.0) < 0.01

    def test_validate_sample_size_pass(self):
        """Test validation passes when N >= 55."""
        df = pd.DataFrame({'species_id': [f'sp_{i}' for i in range(60)]})
        assert validate_sample_size(df, min_n=55) is True

    def test_validate_sample_size_fail(self):
        """Test validation fails when N < 55."""
        df = pd.DataFrame({'species_id': [f'sp_{i}' for i in range(10)]})
        with pytest.raises(RuntimeError, match="Insufficient species after merge"):
            validate_sample_size(df, min_n=55)

    def test_groupkfold_prevention_logic(self, temp_dir, mock_rsa_data, mock_physio_data):
        """
        Verify that the merged output does not contain duplicate species entries
        that could bias GroupKFold. This specifically tests the core requirement of T042.
        """
        output_path = Path(temp_dir) / "merged_gkfold.csv"
        
        # Load data
        rsa_df = pd.read_csv(mock_rsa_data)
        physio_df = pd.read_csv(mock_physio_data)
        
        # Merge
        result = merge_datasets(rsa_df, physio_df, str(output_path))
        
        # Check for duplicates
        duplicates = result[result.duplicated(subset=['species_id'], keep=False)]
        assert duplicates.empty, "Duplicate species entries found: GroupKFold would be biased."
        
        # Check that species_id is the grouping key and is unique
        assert result['species_id'].is_unique, "species_id must be unique for GroupKFold groups."
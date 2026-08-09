"""
Tests for the associational_only metadata flag functionality.

These tests verify that:
1. The flag is correctly added to CSV files
2. The flag is correctly recorded in metadata.yaml
3. The flag is applied to all required output datasets
"""
import pytest
import os
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import yaml

# Add project root to path
project_root = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(project_root / "code"))

from analysis.metadata_utils import (
    load_metadata,
    save_metadata,
    add_associational_only_flag_to_dataset,
    add_associational_only_flag_to_csv,
    flag_all_output_datasets
)


class TestAssociationalOnlyFlag:
    """Tests for the associational_only metadata flag."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)
    
    @pytest.fixture
    def sample_csv(self, temp_dir):
        """Create a sample CSV file for testing."""
        csv_path = Path(temp_dir) / "test_output.csv"
        df = pd.DataFrame({
            'halo_id': [1, 2, 3],
            'axial_ratio': [0.8, 0.6, 0.9],
            'triaxiality': [0.2, 0.4, 0.1]
        })
        df.to_csv(csv_path, index=False)
        return str(csv_path)
    
    @pytest.fixture
    def sample_metadata(self, temp_dir):
        """Create a sample metadata file for testing."""
        metadata_path = Path(temp_dir) / "metadata.yaml"
        metadata = {
            "version": "1.0.0",
            "datasets": {},
            "pipeline_info": {
                "associational_only": False
            }
        }
        with open(metadata_path, 'w') as f:
            yaml.dump(metadata, f)
        return str(metadata_path)
    
    def test_add_flag_to_csv(self, temp_dir, sample_csv):
        """Test that the flag column is added to a CSV file."""
        add_associational_only_flag_to_csv(sample_csv)
        
        # Read the updated CSV
        df = pd.read_csv(sample_csv)
        
        # Verify the flag column exists
        assert 'associational_only' in df.columns
        assert all(df['associational_only'] == 'true')
    
    def test_add_flag_to_metadata(self, temp_dir, sample_metadata):
        """Test that the flag is added to metadata."""
        metadata = load_metadata(sample_metadata)
        updated_metadata = add_associational_only_flag_to_dataset(
            metadata,
            "test_dataset",
            "data/test.csv"
        )
        
        # Verify global flag
        assert updated_metadata['pipeline_info']['associational_only'] is True
        
        # Verify dataset entry
        assert 'test_dataset' in updated_metadata['datasets']
        assert updated_metadata['datasets']['test_dataset']['associational_only'] is True
    
    def test_flag_all_output_datasets(self, temp_dir, sample_csv, sample_metadata):
        """Test that all output datasets are flagged."""
        # Create additional test files
        file2 = Path(temp_dir) / "test2.csv"
        pd.DataFrame({'col': [1]}).to_csv(file2, index=False)
        
        output_files = [sample_csv, str(file2)]
        
        # Flag all files
        updated_metadata = flag_all_output_datasets(sample_metadata, output_files)
        
        # Verify global flag
        assert updated_metadata['pipeline_info']['associational_only'] is True
        
        # Verify all datasets are flagged
        assert len(updated_metadata['datasets']) == 2
        for dataset_name, dataset_info in updated_metadata['datasets'].items():
            assert dataset_info['associational_only'] is True
        
        # Verify CSV files have the column
        for file_path in output_files:
            df = pd.read_csv(file_path)
            assert 'associational_only' in df.columns
            assert all(df['associational_only'] == 'true')
    
    def test_flag_for_nonexistent_file(self, temp_dir, sample_metadata):
        """Test that non-existent files are handled gracefully."""
        nonexistent_file = str(Path(temp_dir) / "nonexistent.csv")
        output_files = [nonexistent_file]
        
        # Should not raise an error
        updated_metadata = flag_all_output_datasets(sample_metadata, output_files)
        
        # Verify no dataset entry was created for the non-existent file
        assert len(updated_metadata['datasets']) == 0
    
    def test_metadata_persistence(self, temp_dir, sample_csv, sample_metadata):
        """Test that metadata changes are persisted to disk."""
        # Flag the dataset
        flag_all_output_datasets(sample_metadata, [sample_csv])
        
        # Reload metadata
        reloaded_metadata = load_metadata(sample_metadata)
        
        # Verify changes are persisted
        assert reloaded_metadata['pipeline_info']['associational_only'] is True
        assert 'test_output' in reloaded_metadata['datasets']
        assert reloaded_metadata['datasets']['test_output']['associational_only'] is True

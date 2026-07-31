"""
Tests for code/analysis/load_data.py
"""
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from pathlib import Path
import json
import tempfile
import os

# Import the functions to test
# Note: We assume the module is importable as 'analysis.load_data' or similar
# Based on the project structure, it's likely 'code.analysis.load_data'
# We'll use a relative import structure assuming tests are run from root
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.load_data import (
    filter_high_quality_complexes,
    subsample_representative_set,
    prepare_complex_metadata,
    MIN_COMPLEXES_REQUIRED
)

class TestFilterHighQualityComplexes:
    def test_filter_resolution(self):
        """Test that complexes with resolution > 2.0 are removed."""
        data = {
            'resolution': [1.5, 2.5, 1.8, 3.0],
            'num_residues': [100, 100, 100, 100],
            'pkd': [10.0, 10.0, 10.0, 10.0]
        }
        df = pd.DataFrame(data)
        result = filter_high_quality_complexes(df)
        
        assert len(result) == 2
        assert all(result['resolution'] <= 2.0)
        
    def test_filter_residues(self):
        """Test that complexes with > 200 residues are removed."""
        data = {
            'resolution': [1.5, 1.5, 1.5, 1.5],
            'num_residues': [100, 250, 150, 300],
            'pkd': [10.0, 10.0, 10.0, 10.0]
        }
        df = pd.DataFrame(data)
        result = filter_high_quality_complexes(df)
        
        assert len(result) == 2
        assert all(result['num_residues'] <= 200)
        
    def test_filter_missing_affinity(self):
        """Test that complexes with missing affinity are removed."""
        data = {
            'resolution': [1.5, 1.5, 1.5],
            'num_residues': [100, 100, 100],
            'pkd': [10.0, None, 10.0]
        }
        df = pd.DataFrame(data)
        result = filter_high_quality_complexes(df)
        
        assert len(result) == 2
        assert result['pkd'].isna().sum() == 0

class TestSubsampleRepresentativeSet:
    def test_subsample_smaller_than_target(self):
        """Test that if data is smaller than target, all is returned."""
        data = {
            'resolution': [1.5, 1.8],
            'num_residues': [100, 100],
            'pkd': [10.0, 11.0],
            'protein_family': ['A', 'B']
        }
        df = pd.DataFrame(data)
        result = subsample_representative_set(df, target_size=10)
        
        assert len(result) == 2
        
    def test_subsample_randomness(self):
        """Test that subsampling is deterministic with seed."""
        data = {
            'resolution': [1.5] * 20,
            'num_residues': [100] * 20,
            'pkd': list(range(20)),
            'protein_family': ['A'] * 20
        }
        df = pd.DataFrame(data)
        
        result1 = subsample_representative_set(df, target_size=5)
        result2 = subsample_representative_set(df, target_size=5)
        
        # Should be identical because of random_state
        assert list(result1['pkd']) == list(result2['pkd'])

class TestPrepareComplexMetadata:
    def test_metadata_conversion(self):
        """Test conversion of DataFrame to metadata list."""
        data = {
            'pdb_id': ['1J22', '1ABC'],
            'resolution': [1.5, 2.0],
            'num_residues': [100, 150],
            'pkd': [10.0, 11.0]
        }
        df = pd.DataFrame(data)
        result = prepare_complex_metadata(df)
        
        assert len(result) == 2
        assert result[0]['pdb_id'] == '1J22'
        assert result[0]['binding_affinity'] == 10.0
        assert result[0]['affinity_type'] == 'pKd'

class TestLoadAndSubsampleIntegration:
    @patch('analysis.load_data.fetch_pdbbind_refined_subset')
    @patch('analysis.load_data.write_json')
    @patch('analysis.load_data.ensure_directory')
    def test_full_pipeline_success(self, mock_ensure, mock_write, mock_fetch):
        """Test the full pipeline with mocked fetch."""
        # Mock data
        mock_df = pd.DataFrame({
            'resolution': [1.5] * 50,
            'num_residues': [100] * 50,
            'pkd': [10.0] * 50,
            'pdb_id': [f'PDB{i}' for i in range(50)]
        })
        mock_fetch.return_value = mock_df
        
        from analysis.load_data import load_and_subsample
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.json"
            result = load_and_subsample(str(output_path))
            
            assert len(result) == 10  # Target size
            mock_write.assert_called_once()
            mock_ensure.assert_called_once()
            
    @patch('analysis.load_data.fetch_pdbbind_refined_subset')
    def test_insufficient_data_error(self, mock_fetch):
        """Test that error is raised if not enough data."""
        mock_df = pd.DataFrame({
            'resolution': [1.5] * 5,
            'num_residues': [100] * 5,
            'pkd': [10.0] * 5,
            'pdb_id': [f'PDB{i}' for i in range(5)]
        })
        mock_fetch.return_value = mock_df
        
        from analysis.load_data import load_and_subsample
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.json"
            with pytest.raises(RuntimeError) as excinfo:
                load_and_subsample(str(output_path))
                
            assert "DataInsufficientError" in str(excinfo.value)
            assert "Minimum required" in str(excinfo.value)

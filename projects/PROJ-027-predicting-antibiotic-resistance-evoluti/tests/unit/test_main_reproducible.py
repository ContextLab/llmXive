"""
Unit tests for main_reproducible.py functionality
"""
import pytest
import json
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.main_reproducible import verify_plasmid_exclusion, verify_checksums
from utils.hash_artifacts import compute_file_hash

class TestVerifyPlasmidExclusion:
    def test_no_plasmid_features(self, tmp_path):
        """Test that feature matrix without plasmid features passes verification"""
        feature_matrix_path = tmp_path / "feature_matrix.csv"
        
        # Create a feature matrix without plasmid features
        data = {
            'isolate_id': ['EC001', 'EC002', 'EC003'],
            'gene_A': [1, 0, 1],
            'gene_B': [0, 1, 0],
            'snp_count': [10, 15, 12],
            'resistance_phenotype': ['resistant', 'sensitive', 'resistant']
        }
        df = pd.DataFrame(data)
        df.to_csv(feature_matrix_path, index=False)
        
        result = verify_plasmid_exclusion(feature_matrix_path)
        assert result is True

    def test_plasmid_features_present(self, tmp_path, caplog):
        """Test that feature matrix with plasmid features fails verification"""
        feature_matrix_path = tmp_path / "feature_matrix.csv"
        
        # Create a feature matrix with plasmid features
        data = {
            'isolate_id': ['EC001', 'EC002', 'EC003'],
            'gene_A': [1, 0, 1],
            'plasmid_repA': [1, 1, 0],
            'plasmid_repB': [0, 1, 1],
            'snp_count': [10, 15, 12],
            'resistance_phenotype': ['resistant', 'sensitive', 'resistant']
        }
        df = pd.DataFrame(data)
        df.to_csv(feature_matrix_path, index=False)
        
        result = verify_plasmid_exclusion(feature_matrix_path)
        assert result is False
        
        # Check that warning was logged
        assert "W003" in caplog.text
        assert "Plasmid features" in caplog.text

    def test_missing_feature_matrix(self, tmp_path):
        """Test that missing feature matrix returns False"""
        feature_matrix_path = tmp_path / "nonexistent.csv"
        
        result = verify_plasmid_exclusion(feature_matrix_path)
        assert result is False

class TestVerifyChecksums:
    def test_checksums_match(self, tmp_path):
        """Test that matching checksums return True"""
        state_path = tmp_path / "state.json"
        
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        # Create state with correct hash
        correct_hash = compute_file_hash(test_file)
        state_data = {
            'hashes': {
                str(test_file): correct_hash
            }
        }
        with open(state_path, 'w') as f:
            json.dump(state_data, f)
        
        # Mock get_paths to return our test file
        import code.main_reproducible as main_module
        original_get_paths = main_module.get_paths
        
        def mock_get_paths():
            return {
                'feature_matrix': test_file,
                'phylogeny_tree': test_file,
                'model_metrics': test_file,
                'final_figures': test_file,
                'state': state_path,
                'data_raw': tmp_path,
                'data_processed': tmp_path,
                'data_models': tmp_path,
                'figures': tmp_path
            }
        
        main_module.get_paths = mock_get_paths
        
        try:
            result = verify_checksums(state_path)
            assert result is True
        finally:
            main_module.get_paths = original_get_paths

    def test_checksums_mismatch(self, tmp_path, caplog):
        """Test that mismatched checksums return False"""
        state_path = tmp_path / "state.json"
        
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        # Create state with wrong hash
        wrong_hash = "wrong_hash_value"
        state_data = {
            'hashes': {
                str(test_file): wrong_hash
            }
        }
        with open(state_path, 'w') as f:
            json.dump(state_data, f)
        
        # Mock get_paths
        import code.main_reproducible as main_module
        original_get_paths = main_module.get_paths
        
        def mock_get_paths():
            return {
                'feature_matrix': test_file,
                'phylogeny_tree': test_file,
                'model_metrics': test_file,
                'final_figures': test_file,
                'state': state_path,
                'data_raw': tmp_path,
                'data_processed': tmp_path,
                'data_models': tmp_path,
                'figures': tmp_path
            }
        
        main_module.get_paths = mock_get_paths
        
        try:
            result = verify_checksums(state_path)
            assert result is False
            
            # Check that error was logged
            assert "Checksum mismatch" in caplog.text
        finally:
            main_module.get_paths = original_get_paths

    def test_missing_state_file(self, tmp_path):
        """Test that missing state file returns True (skip verification)"""
        state_path = tmp_path / "nonexistent_state.json"
        
        result = verify_checksums(state_path)
        assert result is True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

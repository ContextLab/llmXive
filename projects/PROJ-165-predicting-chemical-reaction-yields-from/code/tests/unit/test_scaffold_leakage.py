import pytest
import json
import os
import tempfile
from pathlib import Path
import sys
from unittest.mock import MagicMock, patch

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from scripts.validate_scaffold_leakage import (
    load_splits,
    extract_scaffolds,
    check_leakage
)


class TestScaffoldLeakage:
    """Unit tests for scaffold leakage validation logic."""

    def test_load_splits_success(self):
        """Test loading splits from a valid manifest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create mock manifest
            manifest = {
                'train': {'indices_file': 'train_indices.parquet', 'count': 100},
                'val': {'indices_file': 'val_indices.parquet', 'count': 20},
                'test': {'indices_file': 'test_indices.parquet', 'count': 30}
            }
            
            manifest_path = tmpdir / 'manifest.json'
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f)
            
            # Create mock indices files
            for split in ['train', 'val', 'test']:
                indices_file = tmpdir / f'{split}_indices.parquet'
                # In real implementation, this would be a parquet file
                # Here we just create a placeholder
                indices_file.write_text("dummy")
            
            # Mock load_split_manifest and load_split_indices
            with patch('scripts.validate_scaffold_leakage.load_split_manifest') as mock_manifest, \
                 patch('scripts.validate_scaffold_leakage.load_split_indices') as mock_indices:
                
                mock_manifest.return_value = manifest
                mock_indices.side_effect = lambda x: [1, 2, 3] if 'train' in str(x) else [4, 5] if 'val' in str(x) else [6, 7, 8]
                
                splits = load_splits(manifest_path)
                
                assert 'train' in splits
                assert 'val' in splits
                assert 'test' in splits
                assert len(splits['train']) == 3
                assert len(splits['val']) == 2
                assert len(splits['test']) == 3

    def test_extract_scaffolds(self):
        """Test scaffold extraction logic."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            splits = {
                'train': [1, 2, 3],
                'val': [4, 5],
                'test': [6, 7, 8]
            }
            
            # Mock extract_templates_for_indices
            with patch('scripts.validate_scaffold_leakage.extract_templates_for_indices') as mock_extract:
                mock_extract.side_effect = lambda path, indices: [f'scaffold_{i}' for i in indices]
                
                scaffolds = extract_scaffolds(tmpdir, splits)
                
                assert 'train' in scaffolds
                assert 'val' in scaffolds
                assert 'test' in scaffolds
                assert len(scaffolds['train']) == 3
                assert len(scaffolds['val']) == 2
                assert len(scaffolds['test']) == 3

    def test_check_leakage_no_overlap(self):
        """Test leakage check when there is no overlap."""
        scaffolds = {
            'train': {'scaffold_1', 'scaffold_2', 'scaffold_3'},
            'val': {'scaffold_4', 'scaffold_5'},
            'test': {'scaffold_6', 'scaffold_7'}
        }
        
        has_leakage, details = check_leakage(scaffolds)
        
        assert has_leakage is False
        assert len(details['train_val_overlap']) == 0
        assert len(details['train_test_overlap']) == 0
        assert len(details['val_test_overlap']) == 0

    def test_check_leakage_with_overlap(self):
        """Test leakage check when there is overlap."""
        scaffolds = {
            'train': {'scaffold_1', 'scaffold_2', 'scaffold_3'},
            'val': {'scaffold_2', 'scaffold_4'},  # scaffold_2 overlaps
            'test': {'scaffold_3', 'scaffold_5'}   # scaffold_3 overlaps
        }
        
        has_leakage, details = check_leakage(scaffolds)
        
        assert has_leakage is True
        assert 'scaffold_2' in details['train_val_overlap']
        assert 'scaffold_3' in details['train_test_overlap']
        assert len(details['val_test_overlap']) == 0

    def test_check_leakage_triple_overlap(self):
        """Test leakage check with triple overlap."""
        scaffolds = {
            'train': {'scaffold_1', 'scaffold_2'},
            'val': {'scaffold_1', 'scaffold_3'},
            'test': {'scaffold_1', 'scaffold_4'}
        }
        
        has_leakage, details = check_leakage(scaffolds)
        
        assert has_leakage is True
        assert 'scaffold_1' in details['train_val_overlap']
        assert 'scaffold_1' in details['train_test_overlap']
        assert 'scaffold_1' in details['val_test_overlap']
        assert 'scaffold_1' in details['train_val_test_overlap']
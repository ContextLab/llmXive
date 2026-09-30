import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.datasets.verify_design import (
    DesignVerificationError,
    DesignMetadata,
    validate_metadata_fields,
    validate_design_logic,
    verify_dataset_design,
    verify_all_datasets
)

class TestValidateMetadataFields:
    def test_valid_metadata(self):
        dataset_info = {
            'pre_scan_count': 1,
            'post_scan_count': 1,
            'intervention_type': 'Mindfulness Training',
            'scan_type': 'rs-fMRI'
        }
        is_valid, metadata, errors = validate_metadata_fields(dataset_info)
        
        assert is_valid is True
        assert errors == []
        assert isinstance(metadata, DesignMetadata)
        assert metadata.pre_scan_count == 1
        assert metadata.post_scan_count == 1
        assert metadata.intervention_type == 'Mindfulness Training'
        assert metadata.scan_type == 'rs-fMRI'

    def test_missing_field(self):
        dataset_info = {
            'pre_scan_count': 1,
            'intervention_type': 'Mindfulness'
        }
        is_valid, metadata, errors = validate_metadata_fields(dataset_info)
        
        assert is_valid is False
        assert metadata is None
        assert len(errors) == 2
        assert any('post_scan_count' in e for e in errors)
        assert any('scan_type' in e for e in errors)

    def test_wrong_type(self):
        dataset_info = {
            'pre_scan_count': '1',
            'post_scan_count': 1,
            'intervention_type': 'Mindfulness',
            'scan_type': 'rs-fMRI'
        }
        is_valid, metadata, errors = validate_metadata_fields(dataset_info)
        
        assert is_valid is False
        assert metadata is None
        assert any('pre_scan_count must be int' in e for e in errors)

class TestValidateDesignLogic:
    def test_valid_logic(self):
        metadata = DesignMetadata(
            pre_scan_count=2,
            post_scan_count=2,
            intervention_type='MBSR Program',
            scan_type='resting'
        )
        is_valid, errors = validate_design_logic(metadata)
        
        assert is_valid is True
        assert errors == []

    def test_zero_pre_scan(self):
        metadata = DesignMetadata(
            pre_scan_count=0,
            post_scan_count=2,
            intervention_type='Mindfulness',
            scan_type='rs-fMRI'
        )
        is_valid, errors = validate_design_logic(metadata)
        
        assert is_valid is False
        assert any('pre_scan_count must be > 0' in e for e in errors)

    def test_invalid_intervention_type(self):
        metadata = DesignMetadata(
            pre_scan_count=1,
            post_scan_count=1,
            intervention_type='Yoga',
            scan_type='rs-fMRI'
        )
        is_valid, errors = validate_design_logic(metadata)
        
        assert is_valid is False
        assert any('does not match pattern' in e for e in errors)

    def test_invalid_scan_type(self):
        metadata = DesignMetadata(
            pre_scan_count=1,
            post_scan_count=1,
            intervention_type='MBC',
            scan_type='task-based'
        )
        is_valid, errors = validate_design_logic(metadata)
        
        assert is_valid is False
        assert any('must be one of' in e for e in errors)

    def test_case_insensitive_intervention(self):
        metadata = DesignMetadata(
            pre_scan_count=1,
            post_scan_count=1,
            intervention_type='mbsr',
            scan_type='rs-fMRI'
        )
        is_valid, errors = validate_design_logic(metadata)
        
        assert is_valid is True

class TestVerifyDatasetDesign:
    def test_full_valid_dataset(self):
        dataset_info = {
            'pre_scan_count': 2,
            'post_scan_count': 2,
            'intervention_type': 'Mindfulness-Based Stress Reduction',
            'scan_type': 'rs-fMRI'
        }
        is_valid, metadata, errors = verify_dataset_design(dataset_info)
        
        assert is_valid is True
        assert metadata is not None
        assert errors == []

    def test_invalid_metadata_fields(self):
        dataset_info = {
            'pre_scan_count': 1,
            'post_scan_count': 1
        }
        is_valid, metadata, errors = verify_dataset_design(dataset_info)
        
        assert is_valid is False
        assert metadata is None
        assert len(errors) == 2

    def test_valid_fields_invalid_logic(self):
        dataset_info = {
            'pre_scan_count': 0,
            'post_scan_count': 1,
            'intervention_type': 'Yoga',
            'scan_type': 'task'
        }
        is_valid, metadata, errors = verify_dataset_design(dataset_info)
        
        assert is_valid is False
        assert metadata is not None
        assert len(errors) == 3

class TestVerifyAllDatasets:
    @patch('src.datasets.verify_design.get_data_dir')
    def test_no_design_files(self, mock_get_data_dir):
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_get_data_dir.return_value = tmpdir
            # Create empty raw directory
            Path(tmpdir, 'raw').mkdir()
            
            results = verify_all_datasets(Path(tmpdir) / 'raw')
            
            assert results['total_datasets'] == 0
            assert results['verified_datasets'] == []
            assert results['failed_datasets'] == []

    @patch('src.datasets.verify_design.get_data_dir')
    def test_mixed_results(self, mock_get_data_dir):
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_dir = Path(tmpdir) / 'raw'
            raw_dir.mkdir()
            
            # Valid dataset
            valid_dir = raw_dir / 'ds001'
            valid_dir.mkdir()
            with open(valid_dir / 'design.json', 'w') as f:
                json.dump({
                    'pre_scan_count': 1,
                    'post_scan_count': 1,
                    'intervention_type': 'Mindfulness',
                    'scan_type': 'resting'
                }, f)
            
            # Invalid dataset
            invalid_dir = raw_dir / 'ds002'
            invalid_dir.mkdir()
            with open(invalid_dir / 'design.json', 'w') as f:
                json.dump({
                    'pre_scan_count': 0,
                    'post_scan_count': 1,
                    'intervention_type': 'Yoga',
                    'scan_type': 'task'
                }, f)
            
            mock_get_data_dir.return_value = tmpdir
            results = verify_all_datasets()
            
            assert results['total_datasets'] == 2
            assert results['summary']['verified_count'] == 1
            assert results['summary']['failed_count'] == 1
            assert len(results['verified_datasets']) == 1
            assert len(results['failed_datasets']) == 1

    @patch('src.datasets.verify_design.get_data_dir')
    def test_corrupt_json(self, mock_get_data_dir):
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_dir = Path(tmpdir) / 'raw'
            raw_dir.mkdir()
            
            bad_dir = raw_dir / 'ds001'
            bad_dir.mkdir()
            with open(bad_dir / 'design.json', 'w') as f:
                f.write('not valid json')
            
            mock_get_data_dir.return_value = tmpdir
            results = verify_all_datasets()
            
            assert results['total_datasets'] == 1
            assert results['summary']['failed_count'] == 1
            assert len(results['failed_datasets']) == 1
            assert 'Failed to read design.json' in results['failed_datasets'][0]['error']
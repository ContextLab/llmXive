"""
Unit tests for dataset variable fit verification.
"""

import os
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.datasets.verify_variables import (
    VariableFitResult,
    VariableFitError,
    load_dataset_metadata,
    verify_pre_post_scans,
    verify_dmn_coordinates,
    verify_dataset_variables,
    verify_all_datasets,
    generate_verification_report,
    main,
    DMN_NODES
)
from src.datasets.metadata_schema import DatasetMetadata

class TestVariableFitResult:
    """Tests for VariableFitResult dataclass."""

    def test_valid_result(self):
        result = VariableFitResult(
            dataset_id='ds000001',
            has_pre_scan=True,
            has_post_scan=True,
            pre_scan_count=10,
            post_scan_count=10,
            has_dmn_coords=True,
            dmn_coords_match=True,
            missing_variables=[],
            is_valid=True,
            details={}
        )
        assert result.is_valid is True
        assert result.missing_variables == []

    def test_invalid_result(self):
        result = VariableFitResult(
            dataset_id='ds000002',
            has_pre_scan=False,
            has_post_scan=True,
            pre_scan_count=0,
            post_scan_count=10,
            has_dmn_coords=True,
            dmn_coords_match=True,
            missing_variables=['pre_scan_count'],
            is_valid=False,
            details={}
        )
        assert result.is_valid is False
        assert 'pre_scan_count' in result.missing_variables

class TestLoadDatasetMetadata:
    """Tests for loading dataset metadata."""

    def test_load_existing_metadata(self, tmp_path):
        metadata_dir = tmp_path / 'processed' / 'metadata'
        metadata_dir.mkdir(parents=True)

        metadata_file = metadata_dir / 'ds000001_metadata.json'
        metadata_content = {
            'dataset_id': 'ds000001',
            'pre_scan_count': 10,
            'post_scan_count': 10,
            'intervention_type': 'mindfulness',
            'scan_type': 'resting_state',
            'version': '1.0',
            'dmn_coordinates': {
                'PCC': {'x': 0, 'y': -52, 'z': 26},
                'mPFC': {'x': 0, 'y': 52, 'z': 0},
                'IPL': {'x': 46, 'y': -66, 'z': 36},
                'AngularGyrus': {'x': -46, 'y': -66, 'z': 36}
            }
        }

        with open(metadata_file, 'w') as f:
            json.dump(metadata_content, f)

        result = load_dataset_metadata('ds000001', tmp_path)
        assert result is not None
        assert result.pre_scan_count == 10
        assert result.post_scan_count == 10

    def test_load_missing_metadata(self, tmp_path):
        result = load_dataset_metadata('ds_nonexistent', tmp_path)
        assert result is None

class TestVerifyPrePostScans:
    """Tests for pre/post scan verification."""

    def test_both_scans_present(self):
        metadata = DatasetMetadata(
            dataset_id='test',
            pre_scan_count=10,
            post_scan_count=10,
            intervention_type='mindfulness',
            scan_type='resting_state',
            version='1.0'
        )
        has_pre, has_post, pre_count, post_count, missing = verify_pre_post_scans(metadata)
        assert has_pre is True
        assert has_post is True
        assert pre_count == 10
        assert post_count == 10
        assert missing == []

    def test_missing_pre_scan(self):
        metadata = DatasetMetadata(
            dataset_id='test',
            pre_scan_count=0,
            post_scan_count=10,
            intervention_type='mindfulness',
            scan_type='resting_state',
            version='1.0'
        )
        has_pre, has_post, pre_count, post_count, missing = verify_pre_post_scans(metadata)
        assert has_pre is False
        assert has_post is True
        assert 'pre_scan_count' in missing

    def test_missing_post_scan(self):
        metadata = DatasetMetadata(
            dataset_id='test',
            pre_scan_count=10,
            post_scan_count=0,
            intervention_type='mindfulness',
            scan_type='resting_state',
            version='1.0'
        )
        has_pre, has_post, pre_count, post_count, missing = verify_pre_post_scans(metadata)
        assert has_pre is True
        assert has_post is False
        assert 'post_scan_count' in missing

    def test_missing_both_scans(self):
        metadata = DatasetMetadata(
            dataset_id='test',
            pre_scan_count=0,
            post_scan_count=0,
            intervention_type='mindfulness',
            scan_type='resting_state',
            version='1.0'
        )
        has_pre, has_post, pre_count, post_count, missing = verify_pre_post_scans(metadata)
        assert has_pre is False
        assert has_post is False
        assert len(missing) == 2

class TestVerifyDmnCoordinates:
    """Tests for DMN coordinate verification."""

    def test_valid_dmn_coordinates(self):
        metadata = DatasetMetadata(
            dataset_id='test',
            pre_scan_count=10,
            post_scan_count=10,
            intervention_type='mindfulness',
            scan_type='resting_state',
            version='1.0',
            dmn_coordinates={
                'PCC': {'x': 0, 'y': -52, 'z': 26},
                'mPFC': {'x': 0, 'y': 52, 'z': 0},
                'IPL': {'x': 46, 'y': -66, 'z': 36},
                'AngularGyrus': {'x': -46, 'y': -66, 'z': 36}
            }
        )
        has_coords, coords_match, missing = verify_dmn_coordinates(metadata)
        assert has_coords is True
        assert coords_match is True
        assert missing == []

    def test_missing_dmn_coordinates(self):
        metadata = DatasetMetadata(
            dataset_id='test',
            pre_scan_count=10,
            post_scan_count=10,
            intervention_type='mindfulness',
            scan_type='resting_state',
            version='1.0',
            dmn_coordinates=None
        )
        has_coords, coords_match, missing = verify_dmn_coordinates(metadata)
        assert has_coords is False
        assert coords_match is False
        assert 'dmn_coordinates' in missing

    def test_incomplete_dmn_nodes(self):
        metadata = DatasetMetadata(
            dataset_id='test',
            pre_scan_count=10,
            post_scan_count=10,
            intervention_type='mindfulness',
            scan_type='resting_state',
            version='1.0',
            dmn_coordinates={
                'PCC': {'x': 0, 'y': -52, 'z': 26},
                'mPFC': {'x': 0, 'y': 52, 'z': 0}
                # Missing IPL and AngularGyrus
            }
        )
        has_coords, coords_match, missing = verify_dmn_coordinates(metadata)
        assert has_coords is True
        assert coords_match is False
        assert any('missing_dmn_nodes' in m for m in missing)

    def test_invalid_coord_format(self):
        metadata = DatasetMetadata(
            dataset_id='test',
            pre_scan_count=10,
            post_scan_count=10,
            intervention_type='mindfulness',
            scan_type='resting_state',
            version='1.0',
            dmn_coordinates={
                'PCC': {'x': 0, 'y': -52},  # Missing z
                'mPFC': {'x': 0, 'y': 52, 'z': 0},
                'IPL': {'x': 46, 'y': -66, 'z': 36},
                'AngularGyrus': {'x': -46, 'y': -66, 'z': 36}
            }
        )
        has_coords, coords_match, missing = verify_dmn_coordinates(metadata)
        assert has_coords is True
        assert coords_match is False
        assert any('invalid_coord_format' in m for m in missing)

class TestVerifyDatasetVariables:
    """Tests for complete dataset variable verification."""

    def test_valid_dataset(self, tmp_path):
        metadata_dir = tmp_path / 'processed' / 'metadata'
        metadata_dir.mkdir(parents=True)

        metadata_file = metadata_dir / 'ds000001_metadata.json'
        metadata_content = {
            'dataset_id': 'ds000001',
            'pre_scan_count': 10,
            'post_scan_count': 10,
            'intervention_type': 'mindfulness',
            'scan_type': 'resting_state',
            'version': '1.0',
            'dmn_coordinates': {
                'PCC': {'x': 0, 'y': -52, 'z': 26},
                'mPFC': {'x': 0, 'y': 52, 'z': 0},
                'IPL': {'x': 46, 'y': -66, 'z': 36},
                'AngularGyrus': {'x': -46, 'y': -66, 'z': 36}
            }
        }

        with open(metadata_file, 'w') as f:
            json.dump(metadata_content, f)

        result = verify_dataset_variables('ds000001', tmp_path)
        assert result.is_valid is True
        assert result.has_pre_scan is True
        assert result.has_post_scan is True
        assert result.has_dmn_coords is True
        assert result.dmn_coords_match is True
        assert result.missing_variables == []

    def test_invalid_dataset_missing_scans(self, tmp_path):
        metadata_dir = tmp_path / 'processed' / 'metadata'
        metadata_dir.mkdir(parents=True)

        metadata_file = metadata_dir / 'ds000002_metadata.json'
        metadata_content = {
            'dataset_id': 'ds000002',
            'pre_scan_count': 0,
            'post_scan_count': 10,
            'intervention_type': 'mindfulness',
            'scan_type': 'resting_state',
            'version': '1.0'
        }

        with open(metadata_file, 'w') as f:
            json.dump(metadata_content, f)

        result = verify_dataset_variables('ds000002', tmp_path)
        assert result.is_valid is False
        assert result.has_pre_scan is False
        assert 'pre_scan_count' in result.missing_variables

    def test_missing_metadata_file(self, tmp_path):
        result = verify_dataset_variables('nonexistent', tmp_path)
        assert result.is_valid is False
        assert 'metadata_file' in result.missing_variables

class TestVerifyAllDatasets:
    """Tests for verifying all datasets."""

    def test_verify_multiple_datasets(self, tmp_path):
        metadata_dir = tmp_path / 'processed' / 'metadata'
        metadata_dir.mkdir(parents=True)

        # Create valid metadata
        metadata1 = {
            'dataset_id': 'ds000001',
            'pre_scan_count': 10,
            'post_scan_count': 10,
            'intervention_type': 'mindfulness',
            'scan_type': 'resting_state',
            'version': '1.0',
            'dmn_coordinates': {
                'PCC': {'x': 0, 'y': -52, 'z': 26},
                'mPFC': {'x': 0, 'y': 52, 'z': 0},
                'IPL': {'x': 46, 'y': -66, 'z': 36},
                'AngularGyrus': {'x': -46, 'y': -66, 'z': 36}
            }
        }

        # Create invalid metadata (missing post scans)
        metadata2 = {
            'dataset_id': 'ds000002',
            'pre_scan_count': 10,
            'post_scan_count': 0,
            'intervention_type': 'mindfulness',
            'scan_type': 'resting_state',
            'version': '1.0'
        }

        with open(metadata_dir / 'ds000001_metadata.json', 'w') as f:
            json.dump(metadata1, f)
        with open(metadata_dir / 'ds000002_metadata.json', 'w') as f:
            json.dump(metadata2, f)

        results = verify_all_datasets(tmp_path)
        assert len(results) == 2

        valid_count = sum(1 for r in results if r.is_valid)
        assert valid_count == 1

        result_ids = [r.dataset_id for r in results]
        assert 'ds000001' in result_ids
        assert 'ds000002' in result_ids

class TestGenerateVerificationReport:
    """Tests for report generation."""

    def test_generate_report(self, tmp_path):
        results = [
            VariableFitResult(
                dataset_id='ds000001',
                has_pre_scan=True,
                has_post_scan=True,
                pre_scan_count=10,
                post_scan_count=10,
                has_dmn_coords=True,
                dmn_coords_match=True,
                missing_variables=[],
                is_valid=True,
                details={'test': 'detail'}
            ),
            VariableFitResult(
                dataset_id='ds000002',
                has_pre_scan=False,
                has_post_scan=True,
                pre_scan_count=0,
                post_scan_count=10,
                has_dmn_coords=True,
                dmn_coords_match=True,
                missing_variables=['pre_scan_count'],
                is_valid=False,
                details={}
            )
        ]

        output_path = tmp_path / 'results' / 'variable_verification' / 'report.json'
        generate_verification_report(results, output_path)

        assert output_path.exists()

        with open(output_path, 'r') as f:
            report = json.load(f)

        assert report['verification_summary']['total_datasets'] == 2
        assert report['verification_summary']['valid_datasets'] == 1
        assert report['verification_summary']['invalid_datasets'] == 1
        assert 'PCC' in report['dmn_nodes_reference']

class TestMain:
    """Tests for main entry point."""

    @patch('src.datasets.verify_variables.verify_all_datasets')
    @patch('src.datasets.verify_variables.generate_verification_report')
    @patch('src.datasets.verify_variables.get_data_dir')
    def test_main_success(self, mock_get_dir, mock_generate_report, mock_verify, tmp_path):
        mock_get_dir.return_value = str(tmp_path)
        mock_verify.return_value = [
            VariableFitResult(
                dataset_id='ds000001',
                has_pre_scan=True,
                has_post_scan=True,
                pre_scan_count=10,
                post_scan_count=10,
                has_dmn_coords=True,
                dmn_coords_match=True,
                missing_variables=[],
                is_valid=True,
                details={}
            )
        ]

        main()

        mock_verify.assert_called_once()
        mock_generate_report.assert_called_once()

    @patch('src.datasets.verify_variables.verify_all_datasets')
    @patch('src.datasets.verify_variables.get_data_dir')
    def test_main_no_valid_datasets(self, mock_get_dir, mock_verify, tmp_path):
        mock_get_dir.return_value = str(tmp_path)
        mock_verify.return_value = [
            VariableFitResult(
                dataset_id='ds000001',
                has_pre_scan=False,
                has_post_scan=False,
                pre_scan_count=0,
                post_scan_count=0,
                has_dmn_coords=False,
                dmn_coords_match=False,
                missing_variables=['all'],
                is_valid=False,
                details={}
            )
        ]

        with pytest.raises(VariableFitError, match="No valid datasets"):
            main()
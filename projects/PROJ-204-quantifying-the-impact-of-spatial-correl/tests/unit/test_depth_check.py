"""
Unit tests for depth resolution validation module.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from validation.depth_check import (
    validate_depth_resolution,
    apply_depth_check,
    check_depth_conflicts,
    load_sample_metadata,
    DEFAULT_MAX_BULK_DEPTH,
    DEFAULT_DEPTH_RATIO_THRESHOLD
)


class TestValidateDepthResolution:
    """Tests for individual sample validation logic."""

    def test_valid_depth_within_limits(self):
        """Test sample with valid depth parameters."""
        is_valid, reason = validate_depth_resolution(
            sample_id='S001',
            bulk_depth=1.0,
            surface_layer=0.5
        )
        assert is_valid is True
        assert 'appropriate' in reason.lower()

    def test_bulk_depth_exceeds_max(self):
        """Test sample where bulk depth exceeds maximum."""
        is_valid, reason = validate_depth_resolution(
            sample_id='S002',
            bulk_depth=3.0,
            surface_layer=0.5
        )
        assert is_valid is False
        assert 'exceeds max' in reason

    def test_depth_ratio_exceeds_threshold(self):
        """Test sample where bulk/surface ratio exceeds threshold."""
        is_valid, reason = validate_depth_resolution(
            sample_id='S003',
            bulk_depth=0.8,
            surface_layer=0.1,
            depth_ratio_threshold=0.5
        )
        assert is_valid is False
        assert 'ratio' in reason.lower()

    def test_missing_bulk_depth(self):
        """Test sample with missing bulk depth."""
        is_valid, reason = validate_depth_resolution(
            sample_id='S004',
            bulk_depth=None,
            surface_layer=0.5
        )
        assert is_valid is False
        assert 'missing' in reason.lower()

    def test_missing_surface_layer(self):
        """Test sample with missing surface layer."""
        is_valid, reason = validate_depth_resolution(
            sample_id='S005',
            bulk_depth=1.0,
            surface_layer=None
        )
        assert is_valid is False
        assert 'missing' in reason.lower()

    def test_both_missing(self):
        """Test sample with both depth values missing."""
        is_valid, reason = validate_depth_resolution(
            sample_id='S006',
            bulk_depth=None,
            surface_layer=None
        )
        assert is_valid is False
        assert 'missing' in reason.lower()

    def test_zero_surface_layer(self):
        """Test sample with zero surface layer (edge case)."""
        is_valid, reason = validate_depth_resolution(
            sample_id='S007',
            bulk_depth=0.5,
            surface_layer=0.0
        )
        # Should be valid since we can't compute ratio
        assert is_valid is True


class TestLoadSampleMetadata:
    """Tests for metadata loading functionality."""

    def test_load_valid_metadata(self):
        """Test loading metadata from valid file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("sample_id,bulk_depth_um,surface_layer_um\n")
            f.write("S001,1.0,0.5\n")
            f.write("S002,2.0,0.8\n")
            temp_path = f.name

        try:
            df = load_sample_metadata(Path(temp_path))
            assert len(df) == 2
            assert 'sample_id' in df.columns
            assert 'bulk_depth_um' in df.columns
            assert 'surface_layer_um' in df.columns
        finally:
            os.unlink(temp_path)

    def test_missing_file(self):
        """Test loading from non-existent file."""
        df = load_sample_metadata(Path('/nonexistent/path.csv'))
        assert df.empty

    def test_missing_required_columns(self):
        """Test loading file with missing required columns."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("sample_id,other_col\n")
            f.write("S001,value\n")
            temp_path = f.name

        try:
            df = load_sample_metadata(Path(temp_path))
            assert df.empty
        finally:
            os.unlink(temp_path)


class TestApplyDepthCheck:
    """Tests for full dataset depth check application."""

    def test_apply_to_dataset(self):
        """Test applying depth check to a complete dataset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create dataset
            dataset_path = Path(tmpdir) / 'dataset.csv'
            metadata_path = Path(tmpdir) / 'metadata.csv'
            output_path = Path(tmpdir) / 'output.csv'

            dataset_df = pd.DataFrame({
                'sample_id': ['S001', 'S002', 'S003'],
                'PCE': [15.0, 18.0, 20.0]
            })
            dataset_df.to_csv(dataset_path, index=False)

            metadata_df = pd.DataFrame({
                'sample_id': ['S001', 'S002', 'S003'],
                'bulk_depth_um': [1.0, 3.0, 0.5],
                'surface_layer_um': [0.5, 0.5, 0.3]
            })
            metadata_df.to_csv(metadata_path, index=False)

            result = apply_depth_check(dataset_path, metadata_path, output_path)

            assert 'depth_flag' in result.columns
            assert len(result) == 3
            # S002 should be flagged (bulk_depth 3.0 > max 2.0)
            assert result.loc[result['sample_id'] == 'S002', 'depth_flag'].iloc[0] == 'depth_conflict'
            # S001 and S003 should be valid
            assert result.loc[result['sample_id'] == 'S001', 'depth_flag'].iloc[0] == 'valid'
            assert result.loc[result['sample_id'] == 'S003', 'depth_flag'].iloc[0] == 'valid'

            # Verify file was written
            assert output_path.exists()

    def test_missing_metadata_samples(self):
        """Test handling of samples without metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_path = Path(tmpdir) / 'dataset.csv'
            metadata_path = Path(tmpdir) / 'metadata.csv'
            output_path = Path(tmpdir) / 'output.csv'

            # Dataset with 3 samples
            dataset_df = pd.DataFrame({
                'sample_id': ['S001', 'S002', 'S003'],
                'PCE': [15.0, 18.0, 20.0]
            })
            dataset_df.to_csv(dataset_path, index=False)

            # Metadata only for 2 samples
            metadata_df = pd.DataFrame({
                'sample_id': ['S001', 'S002'],
                'bulk_depth_um': [1.0, 2.0],
                'surface_layer_um': [0.5, 0.8]
            })
            metadata_df.to_csv(metadata_path, index=False)

            result = apply_depth_check(dataset_path, metadata_path, output_path)

            assert len(result) == 3
            # S003 should have missing_metadata flag
            assert result.loc[result['sample_id'] == 'S003', 'depth_flag'].iloc[0] == 'missing_metadata'

    def test_empty_dataset(self):
        """Test applying to empty dataset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_path = Path(tmpdir) / 'dataset.csv'
            metadata_path = Path(tmpdir) / 'metadata.csv'
            output_path = Path(tmpdir) / 'output.csv'

            pd.DataFrame(columns=['sample_id', 'PCE']).to_csv(dataset_path, index=False)
            pd.DataFrame(columns=['sample_id', 'bulk_depth_um', 'surface_layer_um']).to_csv(metadata_path, index=False)

            result = apply_depth_check(dataset_path, metadata_path, output_path)
            assert len(result) == 0


class TestCheckDepthConflicts:
    """Tests for conflict analysis functionality."""

    def test_conflict_analysis(self):
        """Test conflict analysis with mixed flags."""
        df = pd.DataFrame({
            'sample_id': ['S001', 'S002', 'S003', 'S004', 'S005'],
            'depth_flag': ['valid', 'depth_conflict', 'valid', 'missing_metadata', 'depth_conflict']
        })

        summary = check_depth_conflicts(df)

        assert summary['total_samples'] == 5
        assert summary['valid_samples'] == 2
        assert summary['conflict_samples'] == 2
        assert summary['missing_metadata'] == 1
        assert abs(summary['conflict_rate'] - 0.4) < 0.01

    def test_no_conflicts(self):
        """Test analysis with no conflicts."""
        df = pd.DataFrame({
            'sample_id': ['S001', 'S002'],
            'depth_flag': ['valid', 'valid']
        })

        summary = check_depth_conflicts(df)

        assert summary['conflict_samples'] == 0
        assert summary['conflict_rate'] == 0.0

    def test_missing_column(self):
        """Test analysis when flag column is missing."""
        df = pd.DataFrame({
            'sample_id': ['S001', 'S002'],
            'other_col': ['a', 'b']
        })

        summary = check_depth_conflicts(df, flag_column='depth_flag')
        assert 'error' in summary
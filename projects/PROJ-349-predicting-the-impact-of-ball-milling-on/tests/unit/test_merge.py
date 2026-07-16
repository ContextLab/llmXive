"""
Unit tests for data merger and deduplication logic.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from src.exceptions import DataIngestionError
from src.ingest.merge import (
    _calculate_record_hash,
    _jaccard_similarity,
    _normalize_record,
    _resolve_conflict,
    merge_datasets,
    run_merge_pipeline,
)


class TestMergeHelpers:
    """Tests for helper functions in merge module."""

    def test_calculate_record_hash_basic(self):
        """Test hash calculation for a basic record."""
        record = {
            'material_name': 'SiO2',
            'milling_time_hours': 2.0,
            'ball_milling_speed_rpm': 500,
            'material_type': 'ceramic',
            'D10': 10.5,
            'D50': 25.0,
            'D90': 45.0
        }
        
        hash1 = _calculate_record_hash(record)
        hash2 = _calculate_record_hash(record)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length

    def test_calculate_record_hash_different_values(self):
        """Test that different values produce different hashes."""
        record1 = {
            'material_name': 'SiO2',
            'milling_time_hours': 2.0,
            'ball_milling_speed_rpm': 500,
            'material_type': 'ceramic',
            'D10': 10.5,
            'D50': 25.0,
            'D90': 45.0
        }
        
        record2 = {
            'material_name': 'SiO2',
            'milling_time_hours': 2.0,
            'ball_milling_speed_rpm': 500,
            'material_type': 'ceramic',
            'D10': 11.0,  # Different
            'D50': 25.0,
            'D90': 45.0
        }
        
        hash1 = _calculate_record_hash(record1)
        hash2 = _calculate_record_hash(record2)
        
        assert hash1 != hash2

    def test_jaccard_similarity_identical_sets(self):
        """Test Jaccard similarity for identical sets."""
        set1 = {1, 2, 3}
        set2 = {1, 2, 3}
        
        assert _jaccard_similarity(set1, set2) == 1.0

    def test_jaccard_similarity_disjoint_sets(self):
        """Test Jaccard similarity for disjoint sets."""
        set1 = {1, 2, 3}
        set2 = {4, 5, 6}
        
        assert _jaccard_similarity(set1, set2) == 0.0

    def test_jaccard_similarity_partial_overlap(self):
        """Test Jaccard similarity for partially overlapping sets."""
        set1 = {1, 2, 3}
        set2 = {2, 3, 4}
        
        # Intersection: {2, 3}, Union: {1, 2, 3, 4}
        expected = 2 / 4
        assert _jaccard_similarity(set1, set2) == expected

    def test_normalize_record_missing_values(self):
        """Test normalization handles missing values correctly."""
        record = {
            'material_name': 'SiO2',
            'milling_time_hours': None,
            'ball_milling_speed_rpm': '500',
            'material_type': 'CERAMIC',
            'D10': '10.5',
            'D50': None,
            'D90': 45.0
        }
        
        normalized = _normalize_record(record)
        
        assert normalized['material_name'] == 'sio2'
        assert np.isnan(normalized['milling_time_hours'])
        assert normalized['ball_milling_speed_rpm'] == 500.0
        assert normalized['material_type'] == 'ceramic'
        assert normalized['D10'] == 10.5
        assert np.isnan(normalized['D50'])
        assert normalized['D90'] == 45.0

    def test_resolve_conflict_single_value(self):
        """Test conflict resolution with a single value."""
        values = [10.5]
        sources = ['source1']
        
        result, source = _resolve_conflict(values, sources)
        
        assert result == 10.5
        assert source == 'source1'

    def test_resolve_conflict_all_same(self):
        """Test conflict resolution when all values are identical."""
        values = [10.5, 10.5, 10.5]
        sources = ['source1', 'source2', 'source3']
        
        result, source = _resolve_conflict(values, sources)
        
        assert result == 10.5

    def test_resolve_conflict_numeric_mean(self):
        """Test conflict resolution for numeric values takes mean."""
        values = [10.0, 20.0]
        sources = ['source1', 'source2']
        
        result, source = _resolve_conflict(values, sources)
        
        assert result == 15.0

    def test_resolve_conflict_all_null(self):
        """Test conflict resolution when all values are null."""
        values = [None, np.nan, None]
        sources = ['source1', 'source2', 'source3']
        
        result, source = _resolve_conflict(values, sources)
        
        assert np.isnan(result)
        assert source == 'unknown'


class TestMergeDatasets:
    """Tests for the main merge_datasets function."""

    def test_merge_empty_input(self):
        """Test that empty input raises an error."""
        with pytest.raises(DataIngestionError):
            merge_datasets({})

    def test_merge_single_source(self):
        """Test merging a single source."""
        df = pd.DataFrame({
            'material_name': ['SiO2', 'Al2O3'],
            'milling_time_hours': [2.0, 4.0],
            'ball_milling_speed_rpm': [500, 600],
            'material_type': ['ceramic', 'ceramic'],
            'D10': [10.5, 12.0],
            'D50': [25.0, 30.0],
            'D90': [45.0, 55.0]
        })
        
        result = merge_datasets({'source1': df})
        
        assert len(result) == 2
        assert '_source' in result.columns
        assert all(result['_source'] == 'source1')

    def test_merge_multiple_sources_no_conflict(self):
        """Test merging multiple sources with no conflicts."""
        df1 = pd.DataFrame({
            'material_name': ['SiO2'],
            'milling_time_hours': [2.0],
            'ball_milling_speed_rpm': [500],
            'material_type': ['ceramic'],
            'D10': [10.5],
            'D50': [25.0],
            'D90': [45.0]
        })
        
        df2 = pd.DataFrame({
            'material_name': ['Al2O3'],
            'milling_time_hours': [4.0],
            'ball_milling_speed_rpm': [600],
            'material_type': ['ceramic'],
            'D10': [12.0],
            'D50': [30.0],
            'D90': [55.0]
        })
        
        result = merge_datasets({'source1': df1, 'source2': df2})
        
        assert len(result) == 2
        assert result['_source'].tolist() == ['source1', 'source2']

    def test_merge_multiple_sources_with_conflict(self):
        """Test merging multiple sources with conflicting values."""
        df1 = pd.DataFrame({
            'material_name': ['SiO2'],
            'milling_time_hours': [2.0],
            'ball_milling_speed_rpm': [500],
            'material_type': ['ceramic'],
            'D10': [10.0],
            'D50': [25.0],
            'D90': [45.0]
        })
        
        df2 = pd.DataFrame({
            'material_name': ['SiO2'],  # Same material
            'milling_time_hours': [2.0],
            'ball_milling_speed_rpm': [500],
            'material_type': ['ceramic'],
            'D10': [11.0],  # Different D10
            'D50': [25.0],
            'D90': [45.0]
        })
        
        result = merge_datasets({'source1': df1, 'source2': df2})
        
        assert len(result) == 1
        assert '_conflict_resolved' in result.columns
        assert result['_conflict_resolved'].iloc[0] == True
        # D10 should be the mean of 10.0 and 11.0
        assert result['D10'].iloc[0] == 10.5

    def test_merge_with_empty_source(self):
        """Test merging with an empty source dataframe."""
        df1 = pd.DataFrame({
            'material_name': ['SiO2'],
            'milling_time_hours': [2.0],
            'ball_milling_speed_rpm': [500],
            'material_type': ['ceramic'],
            'D10': [10.5],
            'D50': [25.0],
            'D90': [45.0]
        })
        
        df_empty = pd.DataFrame()
        
        result = merge_datasets({'source1': df1, 'empty_source': df_empty})
        
        assert len(result) == 1
        assert result['_source'].iloc[0] == 'source1'

    def test_merge_saves_to_file(self):
        """Test that merge saves output to specified path."""
        df = pd.DataFrame({
            'material_name': ['SiO2'],
            'milling_time_hours': [2.0],
            'ball_milling_speed_rpm': [500],
            'material_type': ['ceramic'],
            'D10': [10.5],
            'D50': [25.0],
            'D90': [45.0]
        })
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_merged"
            result = merge_datasets({'source1': df}, output_path)
            
            parquet_path = output_path.with_suffix('.parquet')
            json_path = output_path.with_suffix('.json')
            
            assert parquet_path.exists()
            assert json_path.exists()
            
            # Verify content
            loaded_df = pd.read_parquet(parquet_path)
            assert len(loaded_df) == 1


class TestRunMergePipeline:
    """Tests for the run_merge_pipeline function."""

    def test_run_merge_pipeline_all_sources(self):
        """Test running the full pipeline with all sources."""
        mp_df = pd.DataFrame({
            'material_name': ['SiO2'],
            'milling_time_hours': [2.0],
            'ball_milling_speed_rpm': [500],
            'material_type': ['ceramic'],
            'D10': [10.5],
            'D50': [25.0],
            'D90': [45.0]
        })
        
        nist_df = pd.DataFrame({
            'material_name': ['Al2O3'],
            'milling_time_hours': [4.0],
            'ball_milling_speed_rpm': [600],
            'material_type': ['ceramic'],
            'D10': [12.0],
            'D50': [30.0],
            'D90': [55.0]
        })
        
        arxiv_df = pd.DataFrame({
            'material_name': ['Fe2O3'],
            'milling_time_hours': [3.0],
            'ball_milling_speed_rpm': [550],
            'material_type': ['metal'],
            'D10': [8.0],
            'D50': [20.0],
            'D90': [35.0]
        })
        
        result = run_merge_pipeline(
            materials_project_df=mp_df,
            nist_df=nist_df,
            arxiv_df=arxiv_df
        )
        
        assert len(result) == 3
        assert set(result['_source'].unique()) == {'materials_project', 'nist', 'arxiv'}

    def test_run_merge_pipeline_empty_sources(self):
        """Test running pipeline with some empty sources."""
        mp_df = pd.DataFrame({
            'material_name': ['SiO2'],
            'milling_time_hours': [2.0],
            'ball_milling_speed_rpm': [500],
            'material_type': ['ceramic'],
            'D10': [10.5],
            'D50': [25.0],
            'D90': [45.0]
        })
        
        result = run_merge_pipeline(
            materials_project_df=mp_df,
            nist_df=None,
            arxiv_df=pd.DataFrame()
        )
        
        assert len(result) == 1
        assert result['_source'].iloc[0] == 'materials_project'

    def test_run_merge_pipeline_no_sources(self):
        """Test running pipeline with no sources raises error."""
        with pytest.raises(DataIngestionError):
            run_merge_pipeline(
                materials_project_df=None,
                nist_df=None,
                arxiv_df=None
            )
"""
Unit tests for the data filtering functions in data_ingestion.py
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import tempfile

from data_ingestion import (
    get_data_source_type_column,
    filter_by_data_source_type,
    filter_by_missing_nutrients,
    filter_by_sample_size,
    write_species_counts_report
)


class TestDataSourceTypeDetection:
    """Tests for data source type column detection"""
    
    def test_detect_primary_column(self):
        """Should detect 'data_source_type' column"""
        df = pd.DataFrame({
            'data_source_type': ['experimental', 'manipulated'],
            'species': ['A', 'B']
        })
        result = get_data_source_type_column(df)
        assert result == 'data_source_type'
    
    def test_detect_alias_source_type(self):
        """Should detect 'source_type' alias"""
        df = pd.DataFrame({
            'source_type': ['experimental'],
            'species': ['A']
        })
        result = get_data_source_type_column(df)
        assert result == 'source_type'
    
    def test_detect_alias_experiment_type(self):
        """Should detect 'experiment_type' alias"""
        df = pd.DataFrame({
            'experiment_type': ['controlled'],
            'species': ['A']
        })
        result = get_data_source_type_column(df)
        assert result == 'experiment_type'
    
    def test_detect_alias_data_origin(self):
        """Should detect 'data_origin' alias"""
        df = pd.DataFrame({
            'data_origin': ['treatment'],
            'species': ['A']
        })
        result = get_data_source_type_column(df)
        assert result == 'data_origin'
    
    def test_raise_error_when_no_column(self):
        """Should raise ValueError when no matching column exists"""
        df = pd.DataFrame({
            'species': ['A', 'B'],
            'root_length': [10.0, 20.0]
        })
        with pytest.raises(ValueError) as exc_info:
            get_data_source_type_column(df)
        assert "Could not detect data source type column" in str(exc_info.value)


class TestFilterByDataSourceType:
    """Tests for filtering by data source type"""
    
    def test_filter_manipulated(self):
        """Should filter out 'manipulated' rows"""
        df = pd.DataFrame({
            'data_source_type': ['experimental', 'manipulated', 'controlled', 'natural'],
            'species': ['A', 'B', 'C', 'D']
        })
        filtered, count = filter_by_data_source_type(df, 'data_source_type')
        assert count == 2
        assert len(filtered) == 2
        assert all(filtered['data_source_type'].isin(['experimental', 'natural']))
    
    def test_case_insensitive(self):
        """Should handle case-insensitive matching"""
        df = pd.DataFrame({
            'data_source_type': ['MANIPULATED', 'Controlled', 'experimental'],
            'species': ['A', 'B', 'C']
        })
        filtered, count = filter_by_data_source_type(df, 'data_source_type')
        assert count == 2
        assert len(filtered) == 1
    
    def test_custom_excluded_types(self):
        """Should use custom excluded types when provided"""
        df = pd.DataFrame({
            'data_source_type': ['experimental', 'treatment', 'natural'],
            'species': ['A', 'B', 'C']
        })
        filtered, count = filter_by_data_source_type(
            df, 'data_source_type', excluded_types=['treatment']
        )
        assert count == 1
        assert len(filtered) == 2


class TestFilterByMissingNutrients:
    """Tests for filtering by missing nutrient values"""
    
    def test_filter_missing_phosphorus(self):
        """Should filter rows with missing phosphorus"""
        df = pd.DataFrame({
            'phosphorus': [10.0, np.nan, 15.0],
            'nitrogen': [20.0, 25.0, 30.0],
            'species': ['A', 'B', 'C']
        })
        filtered, count = filter_by_missing_nutrients(df, p_n_available=True)
        assert count == 1
        assert len(filtered) == 2
    
    def test_filter_missing_nitrogen(self):
        """Should filter rows with missing nitrogen"""
        df = pd.DataFrame({
            'phosphorus': [10.0, 15.0, np.nan],
            'nitrogen': [20.0, np.nan, 30.0],
            'species': ['A', 'B', 'C']
        })
        filtered, count = filter_by_missing_nutrients(df, p_n_available=True)
        assert count == 2
        assert len(filtered) == 1
    
    def test_skip_when_p_n_not_available(self):
        """Should skip filtering when p_n_available is False"""
        df = pd.DataFrame({
            'phosphorus': [10.0, np.nan, 15.0],
            'species': ['A', 'B', 'C']
        })
        filtered, count = filter_by_missing_nutrients(df, p_n_available=False)
        assert count == 0
        assert len(filtered) == 3


class TestFilterBySampleSize:
    """Tests for filtering by species sample size"""
    
    def test_filter_small_species(self):
        """Should exclude species with n < 20"""
        # Create data with varying sample sizes
        data = []
        for i, species in enumerate(['A', 'B', 'C']):
            n = [30, 10, 25][i]  # A: 30, B: 10, C: 25
            data.extend([{'species': species} for _ in range(n)])
        
        df = pd.DataFrame(data)
        filtered, counts = filter_by_sample_size(df, species_col='species', min_n=20)
        
        assert counts['total_species_input'] == 3
        assert counts['excluded_species_count'] == 1
        assert 'B' in counts['excluded_species_list']
        assert len(filtered) == 55  # 30 + 25
        assert counts['rows_excluded_by_sample_size'] == 10
    
    def test_all_species_pass(self):
        """Should keep all species when all meet threshold"""
        df = pd.DataFrame({
            'species': ['A'] * 25 + ['B'] * 30
        })
        filtered, counts = filter_by_sample_size(df, min_n=20)
        assert counts['excluded_species_count'] == 0
        assert len(filtered) == 55
    
    def test_all_species_fail(self):
        """Should exclude all species when none meet threshold"""
        df = pd.DataFrame({
            'species': ['A'] * 10 + ['B'] * 15
        })
        filtered, counts = filter_by_sample_size(df, min_n=20)
        assert counts['excluded_species_count'] == 2
        assert len(filtered) == 0


class TestWriteSpeciesCountsReport:
    """Tests for writing the species counts report"""
    
    def test_write_report(self):
        """Should write valid JSON report"""
        counts = {
            'total_species_input': 100,
            'excluded_species_count': 10,
            'excluded_species_list': ['Species_A', 'Species_B'],
            'rows_excluded_by_sample_size': 50
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'reports' / 'species_counts.json'
            write_species_counts_report(
                counts,
                rows_excluded_by_source=5,
                rows_excluded_by_missing_nutrients=10,
                output_path=output_path
            )
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                report = json.load(f)
            
            assert report['total_species_input'] == 100
            assert report['excluded_species_count'] == 10
            assert 'Species_A' in report['excluded_species_list']
            assert report['rows_excluded_by_source'] == 5
            assert report['rows_excluded_by_missing_nutrients'] == 10
            assert report['rows_excluded_by_sample_size'] == 50

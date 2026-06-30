"""
Unit tests for T030: SubjectMetrics.csv generation.

Tests verify that the metrics pipeline produces a valid CSV file
with the expected columns and data types.
"""

import os
import pandas as pd
import pytest
from pathlib import Path
import numpy as np

# Import the function to test
from metrics import generate_subject_metrics_csv

class TestSubjectMetricsCSV:
    """Test suite for SubjectMetrics.csv generation."""
    
    @pytest.fixture
    def sample_metrics_data(self):
        """Sample metrics data for testing."""
        return {
            'sub-001': {
                'centralities': {
                    'ch1': {'degree': 0.5, 'betweenness': 0.3, 'eigenvector': 0.4},
                    'ch2': {'degree': 0.6, 'betweenness': 0.2, 'eigenvector': 0.5}
                },
                'synchrony': {
                    'N1': 0.15,
                    'N2': 0.22,
                    'N3': 0.18,
                    'REM': 0.25,
                    'Wake': 0.30
                },
                'vif': {
                    'degree': 1.2,
                    'betweenness': 1.5,
                    'eigenvector': 1.8
                },
                'temporal_proximity': True
            },
            'sub-002': {
                'centralities': {
                    'ch1': {'degree': 0.7, 'betweenness': 0.4, 'eigenvector': 0.6},
                    'ch2': {'degree': 0.8, 'betweenness': 0.3, 'eigenvector': 0.7}
                },
                'synchrony': {
                    'N1': 0.16,
                    'N2': 0.24,
                    'N3': 0.19,
                    'REM': 0.26,
                    'Wake': 0.32
                },
                'vif': {
                    'degree': 6.0,  # Above threshold
                    'betweenness': 1.6,
                    'eigenvector': 1.9
                },
                'temporal_proximity': False
            }
        }
    
    @pytest.fixture
    def temp_output_path(self, tmp_path):
        """Temporary output path for testing."""
        return tmp_path / 'SubjectMetrics.csv'
    
    def test_csv_generation(self, sample_metrics_data, temp_output_path):
        """Test that CSV file is generated successfully."""
        generate_subject_metrics_csv(sample_metrics_data, str(temp_output_path))
        
        # Verify file exists
        assert temp_output_path.exists(), "CSV file was not created"
        
        # Verify file is not empty
        assert temp_output_path.stat().st_size > 0, "CSV file is empty"
    
    def test_csv_columns(self, sample_metrics_data, temp_output_path):
        """Test that CSV contains all required columns."""
        generate_subject_metrics_csv(sample_metrics_data, str(temp_output_path))
        
        df = pd.read_csv(temp_output_path)
        
        # Check for required columns
        required_columns = [
            'subject_id',
            'avg_degree_centrality',
            'avg_betweenness_centrality',
            'avg_eigenvector_centrality',
            'pli_n1', 'pli_n2', 'pli_n3', 'pli_rem', 'pli_wake',
            'vif_degree', 'vif_betweenness', 'vif_eigenvector',
            'vif_flag_degree', 'vif_flag_betweenness', 'vif_flag_eigenvector',
            'temporal_proximity_flag'
        ]
        
        for col in required_columns:
            assert col in df.columns, f"Missing required column: {col}"
    
    def test_data_types(self, sample_metrics_data, temp_output_path):
        """Test that data types are correct."""
        generate_subject_metrics_csv(sample_metrics_data, str(temp_output_path))
        
        df = pd.read_csv(temp_output_path)
        
        # Subject ID should be string
        assert df['subject_id'].dtype == 'object', "subject_id should be string"
        
        # Centrality metrics should be numeric
        for col in ['avg_degree_centrality', 'avg_betweenness_centrality', 
                    'avg_eigenvector_centrality']:
            assert pd.api.types.is_numeric_dtype(df[col]), f"{col} should be numeric"
        
        # PLI scores should be numeric
        for col in ['pli_n1', 'pli_n2', 'pli_n3', 'pli_rem', 'pli_wake']:
            assert pd.api.types.is_numeric_dtype(df[col]), f"{col} should be numeric"
        
        # VIF flags should be integer (0 or 1)
        for col in ['vif_flag_degree', 'vif_flag_betweenness', 'vif_flag_eigenvector',
                    'temporal_proximity_flag']:
            assert pd.api.types.is_integer_dtype(df[col]), f"{col} should be integer"
    
    def test_vif_flag_logic(self, sample_metrics_data, temp_output_path):
        """Test that VIF flags are correctly set based on threshold."""
        generate_subject_metrics_csv(sample_metrics_data, str(temp_output_path))
        
        df = pd.read_csv(temp_output_path)
        
        # sub-001 has VIF < 5.0 for all metrics, so flags should be 0
        sub001 = df[df['subject_id'] == 'sub-001'].iloc[0]
        assert sub001['vif_flag_degree'] == 0, "VIF flag should be 0 for degree < 5"
        assert sub001['vif_flag_betweenness'] == 0, "VIF flag should be 0 for betweenness < 5"
        assert sub001['vif_flag_eigenvector'] == 0, "VIF flag should be 0 for eigenvector < 5"
        
        # sub-002 has VIF > 5.0 for degree, so flag should be 1
        sub002 = df[df['subject_id'] == 'sub-002'].iloc[0]
        assert sub002['vif_flag_degree'] == 1, "VIF flag should be 1 for degree > 5"
        assert sub002['vif_flag_betweenness'] == 0, "VIF flag should be 0 for betweenness < 5"
        assert sub002['vif_flag_eigenvector'] == 0, "VIF flag should be 0 for eigenvector < 5"
    
    def test_temporal_proximity_flag(self, sample_metrics_data, temp_output_path):
        """Test that temporal proximity flag is correctly set."""
        generate_subject_metrics_csv(sample_metrics_data, str(temp_output_path))
        
        df = pd.read_csv(temp_output_path)
        
        # sub-001 has temporal_proximity = True
        sub001 = df[df['subject_id'] == 'sub-001'].iloc[0]
        assert sub001['temporal_proximity_flag'] == 1, "Flag should be 1 for True"
        
        # sub-002 has temporal_proximity = False
        sub002 = df[df['subject_id'] == 'sub-002'].iloc[0]
        assert sub002['temporal_proximity_flag'] == 0, "Flag should be 0 for False"
    
    def test_centralities_averaging(self, sample_metrics_data, temp_output_path):
        """Test that centrality metrics are correctly averaged across channels."""
        generate_subject_metrics_csv(sample_metrics_data, str(temp_output_path))
        
        df = pd.read_csv(temp_output_path)
        
        # For sub-001:
        # degree: (0.5 + 0.6) / 2 = 0.55
        # betweenness: (0.3 + 0.2) / 2 = 0.25
        # eigenvector: (0.4 + 0.5) / 2 = 0.45
        sub001 = df[df['subject_id'] == 'sub-001'].iloc[0]
        assert np.isclose(sub001['avg_degree_centrality'], 0.55), "Degree averaging incorrect"
        assert np.isclose(sub001['avg_betweenness_centrality'], 0.25), "Betweenness averaging incorrect"
        assert np.isclose(sub001['avg_eigenvector_centrality'], 0.45), "Eigenvector averaging incorrect"
"""
Unit tests for outlier handling functionality.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json

from src.data.outlier_handler import (
    compute_coordination_numbers,
    flag_outliers,
    save_outlier_summary,
    run_outlier_handling
)


class TestComputeCoordinationNumbers:
    """Tests for compute_coordination_numbers function."""
    
    def test_compute_with_valid_data(self):
        """Test coordination number computation with valid graph data."""
        # Create mock graph data with known structure
        data = {
            'nodes': [
                [{'atomic_number': 6, 'formal_charge': 0}, {'atomic_number': 8, 'formal_charge': 0}],
                [{'atomic_number': 6, 'formal_charge': 0}]
            ],
            'edges': [
                [[0, 1, 1.5]],  # One edge between nodes 0 and 1
                []  # No edges
            ]
        }
        df = pd.DataFrame(data)
        
        # This should not raise an error
        # Note: The actual computation depends on the implementation in graph_construction
        result = compute_coordination_numbers(df)
        
        assert len(result) == len(df)
        assert all(isinstance(val, (int, float, np.integer, np.floating)) or pd.isna(val) for val in result)
    
    def test_compute_with_missing_data(self):
        """Test coordination number computation with missing node/edge data."""
        data = {
            'nodes': [None, [{'atomic_number': 6}]],
            'edges': [None, []]
        }
        df = pd.DataFrame(data)
        
        result = compute_coordination_numbers(df)
        
        assert len(result) == len(df)
        # First should be NaN due to missing data
        assert pd.isna(result.iloc[0])
        # Second might be valid or NaN depending on implementation
        assert isinstance(result.iloc[1], (int, float, np.integer, np.floating)) or pd.isna(result.iloc[1])


class TestFlagOutliers:
    """Tests for flag_outliers function."""
    
    def test_flag_outliers_basic(self):
        """Test basic outlier flagging functionality."""
        # Create mock data with pre-computed coordination numbers
        data = {
            'id': [1, 2, 3, 4, 5],
            'max_coordination_number': [4, 6, 7, 3, 8]
        }
        df = pd.DataFrame(data)
        
        flagged_df, summary = flag_outliers(df, threshold=6)
        
        # Check that outliers are correctly flagged
        assert flagged_df.loc[0, 'is_training_outlier'] == False  # CN=4
        assert flagged_df.loc[1, 'is_training_outlier'] == False  # CN=6 (not > 6)
        assert flagged_df.loc[2, 'is_training_outlier'] == True   # CN=7
        assert flagged_df.loc[3, 'is_training_outlier'] == False  # CN=3
        assert flagged_df.loc[4, 'is_training_outlier'] == True   # CN=8
        
        # Check summary statistics
        assert summary['total_samples'] == 5
        assert summary['outlier_count'] == 2
        assert summary['training_samples'] == 3
        assert summary['threshold'] == 6
        assert 2 in summary['outlier_indices']
        assert 4 in summary['outlier_indices']
    
    def test_flag_outliers_no_outliers(self):
        """Test when there are no outliers."""
        data = {
            'id': [1, 2, 3],
            'max_coordination_number': [4, 5, 6]
        }
        df = pd.DataFrame(data)
        
        flagged_df, summary = flag_outliers(df, threshold=6)
        
        assert summary['outlier_count'] == 0
        assert summary['training_samples'] == 3
        assert len(summary['outlier_indices']) == 0
        assert all(not flagged_df['is_training_outlier'])
    
    def test_flag_outliers_all_outliers(self):
        """Test when all samples are outliers."""
        data = {
            'id': [1, 2, 3],
            'max_coordination_number': [7, 8, 9]
        }
        df = pd.DataFrame(data)
        
        flagged_df, summary = flag_outliers(df, threshold=6)
        
        assert summary['outlier_count'] == 3
        assert summary['training_samples'] == 0
        assert len(summary['outlier_indices']) == 3
        assert all(flagged_df['is_training_outlier'])
    
    def test_flag_outliers_custom_threshold(self):
        """Test with custom threshold."""
        data = {
            'id': [1, 2, 3, 4],
            'max_coordination_number': [4, 5, 6, 7]
        }
        df = pd.DataFrame(data)
        
        # With threshold=5, only CN=6 and CN=7 should be outliers
        flagged_df, summary = flag_outliers(df, threshold=5)
        
        assert summary['outlier_count'] == 2
        assert summary['outlier_indices'] == [2, 3]  # Indices where CN > 5


class TestSaveOutlierSummary:
    """Tests for save_outlier_summary function."""
    
    def test_save_summary(self):
        """Test saving outlier summary to JSON."""
        summary = {
            'total_samples': 100,
            'outlier_count': 10,
            'training_samples': 90,
            'outlier_percentage': 10.0,
            'threshold': 6,
            'outlier_indices': [1, 5, 10]
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "outlier_summary.json"
            save_outlier_summary(summary, output_path)
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                loaded_summary = json.load(f)
            
            assert loaded_summary == summary


class TestRunOutlierHandling:
    """Tests for run_outlier_handling function."""
    
    def test_run_outlier_handling_integration(self):
        """Integration test for the full outlier handling pipeline."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create mock input data
            input_data = {
                'id': [1, 2, 3, 4, 5],
                'nodes': [
                    [{'atomic_number': 6}],
                    [{'atomic_number': 6}, {'atomic_number': 8}],
                    [{'atomic_number': 6}],
                    [{'atomic_number': 6}],
                    [{'atomic_number': 6}]
                ],
                'edges': [
                    [],
                    [[0, 1, 1.5]],
                    [],
                    [],
                    []
                ],
                'max_coordination_number': [4, 6, 7, 3, 8]  # Pre-computed for testing
            }
            input_path = tmpdir / "graphs.parquet"
            pd.DataFrame(input_data).to_parquet(input_path)
            
            output_graphs_path = tmpdir / "graphs_flagged.parquet"
            output_summary_path = tmpdir / "outlier_summary.json"
            
            # Run outlier handling
            summary = run_outlier_handling(
                input_graphs_path=input_path,
                output_graphs_path=output_graphs_path,
                output_summary_path=output_summary_path,
                threshold=6
            )
            
            # Verify outputs
            assert output_graphs_path.exists()
            assert output_summary_path.exists()
            
            # Check summary
            assert summary['total_samples'] == 5
            assert summary['outlier_count'] == 2
            assert summary['training_samples'] == 3
            
            # Check flagged graphs
            flagged_df = pd.read_parquet(output_graphs_path)
            assert 'is_training_outlier' in flagged_df.columns
            assert 'max_coordination_number' in flagged_df.columns
            
            # Verify outlier flags
            assert flagged_df.loc[2, 'is_training_outlier'] == True
            assert flagged_df.loc[4, 'is_training_outlier'] == True
            assert flagged_df.loc[0, 'is_training_outlier'] == False
            assert flagged_df.loc[1, 'is_training_outlier'] == False
            assert flagged_df.loc[3, 'is_training_outlier'] == False

"""
Unit tests for the reporter module (T024).

Tests:
- data_source_type determination logic
- missing confounds detection
- report generation and structure validation
"""
import os
import json
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np
import pytest

# Import from reporter module
from code.models.reporter import (
    determine_data_source_type,
    check_missing_confounds,
    generate_evaluation_report
)

class TestDataSourceTypeDetermination:
    """Test data_source_type logic per T024 requirements."""
    
    def test_synthetic_when_real_count_below_threshold(self):
        """Should return 'Synthetic' when real data count < threshold."""
        predictions_df = pd.DataFrame({
            'alloy_family': ['Al1', 'Al2', 'Al3'],
            'texture_{100}': [1.2, 1.3, 1.4]
        })
        
        # Threshold is 100, real_data_count is 50
        result = determine_data_source_type(predictions_df, real_data_count=50)
        assert result == "Synthetic"
    
    def test_real_when_real_count_above_threshold(self):
        """Should return 'Real' when real data count >= threshold."""
        predictions_df = pd.DataFrame({
            'alloy_family': ['Al1'] * 200,
            'texture_{100}': [1.2] * 200
        })
        
        result = determine_data_source_type(predictions_df, real_data_count=200)
        assert result == "Real"
    
    def test_synthetic_when_synthetic_marker_present(self):
        """Should return 'Synthetic' when synthetic marker is present."""
        predictions_df = pd.DataFrame({
            'alloy_family': ['Al1', 'Al2', 'Al3'],
            'texture_{100}': [1.2, 1.3, 1.4],
            'is_synthetic': [True, True, False]
        })
        
        # Even with some real data, presence of synthetic should trigger Synthetic
        result = determine_data_source_type(predictions_df, real_data_count=150)
        assert result == "Synthetic"
    
    def test_default_to_synthetic_when_uncertain(self):
        """Should default to Synthetic when uncertain."""
        predictions_df = pd.DataFrame({
            'alloy_family': ['Al1'],
            'texture_{100}': [1.2]
        })
        
        # No is_synthetic column, low real count
        result = determine_data_source_type(predictions_df, real_data_count=10)
        assert result == "Synthetic"

class TestMissingConfounds:
    """Test missing confounds detection per SC-004 and FR-012."""
    
    def test_detect_missing_temperature(self):
        """Should detect missing temperature confound."""
        predictions_df = pd.DataFrame({
            'alloy_family': ['Al1'],
            'strain_rate': [1.0]
        })
        
        warnings = check_missing_confounds(predictions_df)
        assert any('temperature' in w for w in warnings)
    
    def test_detect_missing_all_expected_confounds(self):
        """Should detect all missing expected confounds."""
        predictions_df = pd.DataFrame({
            'random_column': [1.0]
        })
        
        warnings = check_missing_confounds(predictions_df)
        assert len(warnings) >= 3  # temperature, strain_rate, alloy_composition
    
    def test_no_warnings_when_all_confounds_present(self):
        """Should return empty list when all confounds present."""
        predictions_df = pd.DataFrame({
            'alloy_family': ['Al1'],
            'temperature': [300.0],
            'strain_rate': [1.0],
            'alloy_composition': [0.5]
        })
        
        warnings = check_missing_confounds(predictions_df)
        # May still have warnings about sample counts, but not missing confounds
        missing_confound_warnings = [w for w in warnings if 'Missing confound' in w]
        assert len(missing_confound_warnings) == 0
    
    def test_warn_about_insufficient_samples(self):
        """Should warn about insufficient samples per family."""
        predictions_df = pd.DataFrame({
            'alloy_family': ['Al1'] * 10 + ['Al2'] * 10,
            'temperature': [300.0] * 20,
            'strain_rate': [1.0] * 20,
            'alloy_composition': [0.5] * 20
        })
        
        warnings = check_missing_confounds(predictions_df)
        assert any('Insufficient samples' in w for w in warnings)

class TestReportGeneration:
    """Test evaluation report generation structure."""
    
    def test_report_structure(self):
        """Test that generated report has required structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create mock predictions
            predictions_df = pd.DataFrame({
                'alloy_family': ['Al1'] * 50 + ['Al2'] * 50 + ['Al3'] * 50,
                'temperature': [300.0] * 150,
                'strain_rate': [1.0] * 150,
                'alloy_composition': [0.5] * 150,
                'texture_{100}': [1.2 + i * 0.01 for i in range(150)],
                'texture_{110}': [1.1 + i * 0.01 for i in range(150)],
                'texture_{111}': [1.0 + i * 0.01 for i in range(150)],
                'is_synthetic': [True] * 150
            })
            
            predictions_path = tmpdir_path / "predictions.csv"
            output_path = tmpdir_path / "evaluation_report.json"
            
            predictions_df.to_csv(predictions_path, index=False)
            
            # Generate report
            report = generate_evaluation_report(
                predictions_path=predictions_path,
                output_path=output_path,
                real_data_count=0
            )
            
            # Verify structure
            assert "report_metadata" in report
            assert "per_family_metrics" in report
            assert "warnings" in report
            assert "summary" in report
            
            # Verify data_source_type
            assert report["report_metadata"]["data_source_type"] == "Synthetic"
            
            # Verify output file exists
            assert output_path.exists()
            
            # Verify JSON is valid
            with open(output_path, 'r') as f:
                loaded_report = json.load(f)
                assert loaded_report == report
    
    def test_report_with_real_data(self):
        """Test report generation with real data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create mock predictions with real data
            predictions_df = pd.DataFrame({
                'alloy_family': ['Al1'] * 200,
                'temperature': [300.0] * 200,
                'strain_rate': [1.0] * 200,
                'alloy_composition': [0.5] * 200,
                'texture_{100}': [1.2 + i * 0.01 for i in range(200)],
                'is_synthetic': [False] * 200
            })
            
            predictions_path = tmpdir_path / "predictions.csv"
            output_path = tmpdir_path / "evaluation_report.json"
            
            predictions_df.to_csv(predictions_path, index=False)
            
            # Generate report
            report = generate_evaluation_report(
                predictions_path=predictions_path,
                output_path=output_path,
                real_data_count=200
            )
            
            # Should be Real since real_data_count >= threshold
            assert report["report_metadata"]["data_source_type"] == "Real"

class TestIntegration:
    """Integration tests for the reporter module."""
    
    def test_full_report_generation_workflow(self):
        """Test complete workflow from predictions to report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create realistic mock data
            np.random.seed(42)
            n_samples = 300
            
            predictions_df = pd.DataFrame({
                'alloy_family': np.random.choice(['Al1', 'Al2', 'Al3'], n_samples),
                'temperature': np.random.uniform(250, 400, n_samples),
                'strain_rate': np.random.uniform(0.5, 2.0, n_samples),
                'alloy_composition': np.random.uniform(0.3, 0.7, n_samples),
                'texture_{100}': np.random.uniform(0.8, 1.5, n_samples),
                'texture_{110}': np.random.uniform(0.8, 1.5, n_samples),
                'texture_{111}': np.random.uniform(0.8, 1.5, n_samples),
                'is_synthetic': [True] * n_samples
            })
            
            predictions_path = tmpdir_path / "predictions.csv"
            output_path = tmpdir_path / "evaluation_report.json"
            
            predictions_df.to_csv(predictions_path, index=False)
            
            # Generate report
            report = generate_evaluation_report(
                predictions_path=predictions_path,
                output_path=output_path,
                real_data_count=0
            )
            
            # Verify all required sections
            assert "report_metadata" in report
            assert "per_family_metrics" in report
            assert "warnings" in report
            assert "summary" in report
            
            # Verify per-family metrics exist for all families
            families_in_data = predictions_df['alloy_family'].unique()
            families_in_report = list(report["per_family_metrics"].keys())
            
            for family in families_in_data:
                assert family in families_in_report
            
            # Verify metrics contain expected keys
            for family, metrics in report["per_family_metrics"].items():
                assert "R2" in metrics or "r2" in metrics
                assert "MAE" in metrics or "mae" in metrics
                assert "RMSE" in metrics or "rmse" in metrics
    
    def test_report_with_insufficient_samples_per_family(self):
        """Test report generation when some families have insufficient samples."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create data with one family having insufficient samples
            predictions_df = pd.DataFrame({
                'alloy_family': ['Al1'] * 100 + ['Al2'] * 100 + ['Al3'] * 10,
                'temperature': [300.0] * 210,
                'strain_rate': [1.0] * 210,
                'alloy_composition': [0.5] * 210,
                'texture_{100}': [1.2] * 210,
                'is_synthetic': [True] * 210
            })
            
            predictions_path = tmpdir_path / "predictions.csv"
            output_path = tmpdir_path / "evaluation_report.json"
            
            predictions_df.to_csv(predictions_path, index=False)
            
            # Generate report
            report = generate_evaluation_report(
                predictions_path=predictions_path,
                output_path=output_path,
                real_data_count=0
            )
            
            # Should have warning about Al3
            warnings = report["warnings"]["missing_confounds"]
            assert any('Al3' in w and 'Insufficient samples' in w for w in warnings)
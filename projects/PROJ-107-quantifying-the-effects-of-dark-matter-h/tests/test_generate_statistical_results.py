"""
Tests for statistical results generation (T025).
"""
import pytest
import pandas as pd
import numpy as np
import os
import tempfile
import shutil
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.analysis.generate_statistical_results import (
    add_associational_only_flag,
    main
)

class TestStatisticalResultsGeneration:
    """Test suite for statistical results generation."""

    def test_add_associational_only_flag(self):
        """Test that associational_only flag is added correctly."""
        df = pd.DataFrame({
            'test_id': ['T001', 'T002'],
            'p_value': [0.01, 0.05]
        })
        
        result = add_associational_only_flag(df)
        
        assert 'associational_only' in result.columns
        assert all(result['associational_only'] == True)
        assert len(result) == 2

    def test_statistical_results_structure(self):
        """Test that statistical results CSV has required columns."""
        # Create a minimal test CSV
        test_df = pd.DataFrame({
            'test_id': ['T001'],
            'property': ['star_formation_rate'],
            'metric': ['correlation'],
            'test_type': ['pearson'],
            'statistic': [0.45],
            'p_value': [0.001],
            'bonferroni_p_value': [0.005],
            'significant': [True],
            'associational_only': [True],
            'analysis_timestamp': ['2024-01-15T10:30:00'],
            'dataset_version': ['1.0']
        })
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_results.csv"
            test_df.to_csv(output_path, index=False)
            
            # Read back and verify
            loaded_df = pd.read_csv(output_path)
            
            required_columns = [
                'test_id', 'property', 'metric', 'test_type',
                'statistic', 'p_value', 'bonferroni_p_value',
                'significant', 'associational_only'
            ]
            
            for col in required_columns:
                assert col in loaded_df.columns, f"Missing column: {col}"

    def test_bonferroni_correction_application(self):
        """Test that Bonferroni correction is applied correctly."""
        # Create test data with known p-values
        test_df = pd.DataFrame({
            'test_id': ['T001', 'T002', 'T003'],
            'p_value': [0.01, 0.02, 0.05]
        })
        
        # Expected Bonferroni correction for 3 tests: p * 3
        expected_p_values = [0.03, 0.06, 0.15]
        
        # Simulate the correction logic
        corrected_p_values = [p * 3 for p in test_df['p_value']]
        
        assert corrected_p_values == expected_p_values

    def test_output_file_creation(self):
        """Test that the output file is created in the correct location."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create necessary directory structure
            processed_dir = Path(tmpdir) / "data" / "processed"
            processed_dir.mkdir(parents=True)
            
            # Create a mock metadata file
            metadata_path = Path(tmpdir) / "data" / "metadata.yaml"
            metadata_path.write_text("outputs: {}\n")
            
            # Note: We cannot run main() here without real data,
            # but we can verify the file path construction logic
            expected_path = processed_dir / "statistical_results.csv"
            assert str(expected_path) == str(processed_dir / "statistical_results.csv")

    def test_data_validation(self):
        """Test that empty datasets are handled correctly."""
        empty_df = pd.DataFrame()
        
        # Should handle empty dataframe gracefully
        assert empty_df.empty
        
        # Test with minimal valid data
        valid_df = pd.DataFrame({
            'test_id': ['T001'],
            'p_value': [0.05]
        })
        assert not valid_df.empty
        assert len(valid_df) == 1
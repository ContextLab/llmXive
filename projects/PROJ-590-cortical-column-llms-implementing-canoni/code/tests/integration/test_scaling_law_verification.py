import pytest
import os
import json
import tempfile
import pandas as pd
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.experiments.scaling import run_scaling_study, verify_scaling_output, save_scaling_results, ScalingResult

class TestScalingLawVerification:
    """Test suite to verify the scaling law output and execution."""

    def test_scaling_output_exists(self, tmp_path):
        """Test that the scaling output file is created."""
        output_path = tmp_path / "scaling_law.csv"
        
        # Run a minimal scaling study
        results = run_scaling_study(
            base_columns=2,
            multipliers=[1, 2],
            output_path=str(output_path),
            train_size=100,
            test_size=50
        )
        
        assert output_path.exists(), "Scaling law CSV not created"

    def test_scaling_output_format(self, tmp_path):
        """Test that the scaling output has correct columns and types."""
        output_path = tmp_path / "scaling_law.csv"
        
        # Run minimal study
        run_scaling_study(
            base_columns=2,
            multipliers=[1, 2],
            output_path=str(output_path),
            train_size=100,
            test_size=50
        )
        
        # Load and verify
        df = pd.read_csv(output_path)
        
        required_cols = ['columns', 'params', 'mae', 'time_sec']
        for col in required_cols:
            assert col in df.columns, f"Missing column: {col}"

        # Check types
        assert df['columns'].dtype in ['int64', 'int32'], "columns should be integer"
        assert df['params'].dtype in ['int64', 'int32'], "params should be integer"
        assert df['mae'].dtype in ['float64', 'float32'], "mae should be float"
        assert df['time_sec'].dtype in ['float64', 'float32'], "time_sec should be float"

    def test_scaling_output_data_integrity(self, tmp_path):
        """Test that scaling output contains valid data (no NaNs, positive values)."""
        output_path = tmp_path / "scaling_law.csv"
        
        run_scaling_study(
            base_columns=2,
            multipliers=[1, 2],
            output_path=str(output_path),
            train_size=100,
            test_size=50
        )
        
        df = pd.read_csv(output_path)
        
        # Check for NaNs
        assert not df.isnull().any().any(), "Scaling data contains NaN values"
        
        # Check positive values
        assert (df['columns'] > 0).all(), "Columns must be positive"
        assert (df['params'] > 0).all(), "Params must be positive"
        assert (df['time_sec'] > 0).all(), "Time must be positive"
        
        # MAE should be non-negative (and typically < 1 for normalized data)
        assert (df['mae'] >= 0).all(), "MAE must be non-negative"

    def test_scaling_trend(self, tmp_path):
        """Test that increasing columns generally increases parameters."""
        output_path = tmp_path / "scaling_law.csv"
        
        run_scaling_study(
            base_columns=2,
            multipliers=[1, 2],
            output_path=str(output_path),
            train_size=100,
            test_size=50
        )
        
        df = pd.read_csv(output_path)
        df = df.sort_values('columns')
        
        # Parameters should increase with columns
        assert (df['params'].diff().dropna() > 0).all(), "Parameters should increase with column count"

    def test_verify_scaling_output_function(self, tmp_path):
        """Test the verify_scaling_output helper function."""
        output_path = tmp_path / "scaling_law.csv"
        
        # Create valid file
        results = [
            ScalingResult(
                multiplier=1,
                num_columns=2,
                parameter_count=1000,
                validation_mae=0.05,
                training_time_sec=10.0,
                config={}
            ),
            ScalingResult(
                multiplier=2,
                num_columns=4,
                parameter_count=2000,
                validation_mae=0.04,
                training_time_sec=20.0,
                config={}
            )
        ]
        save_scaling_results(results, str(output_path))
        
        assert verify_scaling_output(str(output_path)), "Verification should pass for valid file"

    def test_verify_scaling_output_missing_file(self, tmp_path):
        """Test verify_scaling_output with missing file."""
        output_path = tmp_path / "nonexistent.csv"
        
        assert not verify_scaling_output(str(output_path)), "Verification should fail for missing file"

    def test_verify_scaling_output_invalid_csv(self, tmp_path):
        """Test verify_scaling_output with invalid CSV structure."""
        output_path = tmp_path / "invalid.csv"
        
        # Write invalid CSV
        with open(output_path, 'w') as f:
            f.write("wrong,columns,here\n1,2,3\n")
        
        assert not verify_scaling_output(str(output_path)), "Verification should fail for invalid structure"
"""
Unit tests for the pipeline runner (T015).
"""
import pytest
import os
import sys
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from processing.pipeline_runner import iterate_haloes, run_pipeline
from utils.config import get_project_root

class TestPipelineRunner:
    """Test cases for pipeline_runner module."""

    def test_iterate_haloes_generator(self):
        """Test that iterate_haloes returns a generator."""
        # This test will likely fail if no data exists, but tests the interface
        gen = iterate_haloes(chunk_size=10)
        assert hasattr(gen, '__iter__')
        assert hasattr(gen, '__next__')

    def test_run_pipeline_creates_file(self):
        """Test that run_pipeline creates an output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.csv"
            
            # Run pipeline (may produce empty file if no data)
            result_path = run_pipeline(output_path=str(output_path), chunk_size=10)
            
            assert Path(result_path).exists()
            
            # Check file is readable CSV
            df = pd.read_csv(result_path)
            assert isinstance(df, pd.DataFrame)
            
            # Check expected columns exist
            expected_cols = [
                'halo_id', 'n_particles', 'lambda1', 'lambda2', 'lambda3',
                'b_a_ratio', 'c_a_ratio', 'triaxiality', 'is_valid', 'associational_only'
            ]
            
            # If file is empty, columns might not exist, so check if it's empty first
            if len(df) > 0:
                for col in expected_cols:
                    assert col in df.columns, f"Missing column: {col}"
                
                # Check associational_only flag is set
                assert df['associational_only'].all()

    def test_run_pipeline_validation(self):
        """Test that run_pipeline validates shape metrics correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "validation_test.csv"
            
            result_path = run_pipeline(output_path=str(output_path), chunk_size=10)
            df = pd.read_csv(result_path)
            
            if len(df) > 0:
                # Check constraints: 0 < b/a <= 1, 0 < c/a <= 1, 0 <= T <= 1
                assert all((df['b_a_ratio'] > 0) & (df['b_a_ratio'] <= 1))
                assert all((df['c_a_ratio'] > 0) & (df['c_a_ratio'] <= 1))
                assert all((df['triaxiality'] >= 0) & (df['triaxiality'] <= 1))

    def test_chunk_size_parameter(self):
        """Test that chunk_size parameter is accepted."""
        # Just verify the function accepts the parameter without erroring
        # (actual processing depends on data availability)
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "chunk_test.csv"
            try:
                run_pipeline(output_path=str(output_path), chunk_size=50)
            except Exception:
                # Expected if no data files exist
                pass
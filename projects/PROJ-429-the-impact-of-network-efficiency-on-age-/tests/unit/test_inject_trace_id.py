"""
Unit tests for code/inject_trace_id.py
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import pytest

# We need to mock the imports that might fail or are heavy
# But since we are testing the logic, we can import the module directly
# assuming the environment is set up.

# Add parent to path to allow imports
import sys
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "code"))

from inject_trace_id import generate_trace_id, inject_trace_id

class TestGenerateTraceId:
    def test_trace_id_generation_structure(self):
        """Test that generate_trace_id returns a valid hex string."""
        # This test might fail if files don't exist, but we check the type/length
        # In a real CI, these files should exist.
        # We will catch the error if files are missing and just check the type if possible,
        # or skip if environment is not fully set up.
        try:
            trace_id = generate_trace_id()
            assert isinstance(trace_id, str)
            assert len(trace_id) == 64  # SHA-256 hex length
            assert all(c in '0123456789abcdef' for c in trace_id)
        except FileNotFoundError as e:
            # If files are missing (e.g. in a partial test run), we skip
            pytest.skip(f"Missing required files for trace generation: {e}")

    def test_trace_id_determinism(self):
        """Test that running twice on same files yields same ID."""
        try:
            id1 = generate_trace_id()
            id2 = generate_trace_id()
            assert id1 == id2
        except FileNotFoundError:
            pytest.skip("Missing files for determinism test")

class TestInjectTraceId:
    def test_inject_creates_column(self, tmp_path):
        """Test that inject_trace_id adds the column correctly."""
        input_file = tmp_path / "input.csv"
        output_file = tmp_path / "output.csv"
        
        # Create dummy data
        data = {
            "subject_id": [1, 2, 3],
            "global_efficiency": [0.5, 0.6, 0.7],
            "age": [20, 30, 40]
        }
        df = pd.DataFrame(data)
        df.to_csv(input_file, index=False)
        
        trace_id = "a" * 64
        
        inject_trace_id(input_file, output_file, trace_id)
        
        assert output_file.exists()
        result_df = pd.read_csv(output_file)
        
        assert 'trace_id' in result_df.columns
        assert result_df['trace_id'].iloc[0] == trace_id
        assert result_df['trace_id'].iloc[1] == trace_id
        assert result_df['trace_id'].iloc[2] == trace_id
        
        # Check original columns are preserved
        assert 'subject_id' in result_df.columns
        assert 'global_efficiency' in result_df.columns

    def test_inject_overwrites_existing_column(self, tmp_path):
        """Test that if trace_id exists, it is overwritten."""
        input_file = tmp_path / "input.csv"
        output_file = tmp_path / "output.csv"
        
        data = {
            "subject_id": [1],
            "trace_id": ["old_id"]
        }
        pd.DataFrame(data).to_csv(input_file, index=False)
        
        new_trace_id = "b" * 64
        inject_trace_id(input_file, output_file, new_trace_id)
        
        result_df = pd.read_csv(output_file)
        assert result_df['trace_id'].iloc[0] == new_trace_id
        assert result_df['trace_id'].iloc[0] != "old_id"
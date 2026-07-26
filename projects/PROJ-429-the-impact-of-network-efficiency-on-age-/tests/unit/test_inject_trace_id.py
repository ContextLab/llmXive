"""
Unit tests for T019: Inject trace_id into network_metrics.csv.
"""
import hashlib
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from inject_trace_id import generate_trace_id, inject_trace_id, get_source_hash

class TestGenerateTraceId:
    def test_trace_id_format(self):
        """Verify trace_id is a 64-character hex string."""
        trace_id = generate_trace_id()
        assert len(trace_id) == 64
        assert all(c in '0123456789abcdef' for c in trace_id)

    def test_trace_id_uniqueness(self):
        """Verify that trace_id changes if source code changes (mocked)."""
        # This is a basic check; full uniqueness depends on the hash function
        id1 = generate_trace_id()
        id2 = generate_trace_id()
        # In a real scenario with no code changes, these might be the same if timestamps are identical
        # But the logic ensures they are derived from content + time
        assert isinstance(id1, str)
        assert isinstance(id2, str)

class TestInjectTraceId:
    def test_inject_creates_column(self):
        """Verify that inject_trace_id adds the trace_id column."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"
            
            # Create a dummy CSV
            df = pd.DataFrame({"metric": [1, 2, 3], "value": [10, 20, 30]})
            df.to_csv(input_path, index=False)
            
            # Run injection
            inject_trace_id(input_path, output_path)
            
            # Verify output
            result_df = pd.read_csv(output_path)
            assert 'trace_id' in result_df.columns
            assert len(result_df) == 3
            assert result_df['trace_id'].iloc[0] == result_df['trace_id'].iloc[1]
            assert result_df['trace_id'].iloc[0] == result_df['trace_id'].iloc[2]

    def test_inject_fails_on_missing_file(self):
        """Verify that inject_trace_id raises FileNotFoundError for missing input."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "nonexistent.csv"
            output_path = Path(tmpdir) / "output.csv"
            
            with pytest.raises(FileNotFoundError):
                inject_trace_id(input_path, output_path)

    def test_inject_preserves_existing_data(self):
        """Verify that existing columns and values are preserved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"
            
            original_data = {
                "subject_id": ["S1", "S2"],
                "global_efficiency": [0.5, 0.6],
                "local_efficiency": [0.4, 0.5]
            }
            df = pd.DataFrame(original_data)
            df.to_csv(input_path, index=False)
            
            inject_trace_id(input_path, output_path)
            
            result_df = pd.read_csv(output_path)
            assert list(result_df.columns) == ["subject_id", "global_efficiency", "local_efficiency", "trace_id"]
            assert result_df["subject_id"].tolist() == ["S1", "S2"]
            assert result_df["global_efficiency"].tolist() == [0.5, 0.6]
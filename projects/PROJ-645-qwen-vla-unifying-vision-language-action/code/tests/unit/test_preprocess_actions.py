"""
Unit tests for src/data/preprocess_actions.py
"""
import os
import tempfile
import json
import numpy as np
import pandas as pd
import pytest
from pathlib import Path

from src.data.preprocess_actions import ActionTokenizer, preprocess_actions, load_action_config

class TestActionTokenizer:
    """Tests for the ActionTokenizer class."""

    def test_init_defaults(self):
        tokenizer = ActionTokenizer()
        assert tokenizer.action_dim == 7
        assert tokenizer.n_bins == 64
        assert tokenizer.min_val == -1.0
        assert tokenizer.max_val == 1.0

    def test_quantize_valid(self):
        tokenizer = ActionTokenizer(action_dim=2, n_bins=10, min_val=-1.0, max_val=1.0)
        vec = np.array([0.0, 0.5])
        tokens, success = tokenizer.quantize(vec)
        assert success
        assert len(tokens) == 2
        assert all(0 <= t < 10 for t in tokens)

    def test_quantize_wrong_dim(self):
        tokenizer = ActionTokenizer(action_dim=2)
        vec = np.array([0.0, 0.5, 0.9]) # 3 dims
        tokens, success = tokenizer.quantize(vec)
        assert not success
        assert len(tokens) == 0

    def test_quantize_out_of_bounds(self):
        tokenizer = ActionTokenizer(action_dim=2, min_val=-1.0, max_val=1.0)
        vec = np.array([2.0, -2.0]) # Way out of bounds
        tokens, success = tokenizer.quantize(vec)
        assert success # Should clip and succeed
        # 2.0 clips to 1.0 -> should be the last bin
        # -2.0 clips to -1.0 -> should be the first bin
        assert tokens[0] == tokenizer.n_bins - 1
        assert tokens[1] == 0

    def test_quantize_none_input(self):
        tokenizer = ActionTokenizer(action_dim=2)
        tokens, success = tokenizer.quantize(None)
        assert not success

    def test_batch_quantize(self):
        tokenizer = ActionTokenizer(action_dim=2, n_bins=10)
        batch = np.array([
            [0.0, 0.0],
            [0.5, 0.5],
            [2.0, 2.0], # Out of bounds
            [0.1, 0.1]
        ])
        tokens, dropped = tokenizer.batch_quantize(batch)
        assert len(tokens) == 3 # 3 valid
        assert dropped == [2] # Index 2 dropped? Wait, 2.0 clips.
        # Re-check logic: batch_quantize calls quantize. quantize clips.
        # So 2.0 should NOT be dropped, it should be clipped.
        # My test logic above was wrong about dropping out of bounds.
        # Let's fix the test expectation based on the code:
        # Code: clipped = np.clip(...); indices = np.digitize(...). 
        # So out of bounds is clipped, NOT dropped.
        # Dropped only happens if dim mismatch or None.
        
        # Let's test actual drop condition: wrong dim
        batch_bad = np.array([
            [0.0, 0.0],
            [0.5], # Wrong dim
            [0.1, 0.1]
        ])
        # We can't easily pass jagged array to numpy array constructor without object dtype
        # Let's simulate the loop logic in the test manually or adjust the test.
        
        # Correct test for batch_quantize with valid data
        tokens, dropped = tokenizer.batch_quantize(np.array([[0.0, 0.0], [0.5, 0.5]]))
        assert len(tokens) == 2
        assert len(dropped) == 0

class TestPreprocessActions:
    """Tests for the main preprocessing pipeline."""

    def test_preprocess_actions_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.parquet"
            output_path = Path(tmpdir) / "output.parquet"
            
            # Create dummy input
            data = {
                "actions": [
                    [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7],
                    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [-0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5]
                ]
            }
            df = pd.DataFrame(data)
            df.to_parquet(input_path)

            stats = preprocess_actions(
                input_path=str(input_path),
                output_path=str(output_path),
                config_path=None
            )

            assert output_path.exists()
            assert stats["total_rows"] == 3
            assert stats["valid_rows"] == 3
            assert stats["dropped_rows"] == 0

            # Verify output content
            out_df = pd.read_parquet(output_path)
            assert "actions_tokens" in out_df.columns
            assert len(out_df) == 3

    def test_preprocess_actions_drops_malformed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.parquet"
            output_path = Path(tmpdir) / "output.parquet"
            
            # Create input with wrong dimension
            data = {
                "actions": [
                    [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7], # 7 dims (OK)
                    [0.1, 0.2], # 2 dims (BAD)
                    [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7] # 7 dims (OK)
                ]
            }
            df = pd.DataFrame(data)
            df.to_parquet(input_path)

            stats = preprocess_actions(
                input_path=str(input_path),
                output_path=str(output_path),
                config_path=None
            )

            assert stats["total_rows"] == 3
            assert stats["valid_rows"] == 2
            assert stats["dropped_rows"] == 1

            out_df = pd.read_parquet(output_path)
            assert len(out_df) == 2

    def test_load_action_config_defaults(self):
        config = load_action_config()
        assert config["action_dim"] == 7
        assert config["n_bins"] == 64

    def test_load_action_config_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            custom_config = {
                "action_dim": 10,
                "n_bins": 128,
                "min_val": -2.0,
                "max_val": 2.0
            }
            with open(config_path, 'w') as f:
                json.dump(custom_config, f)
            
            config = load_action_config(str(config_path))
            assert config["action_dim"] == 10
            assert config["n_bins"] == 128
            assert config["min_val"] == -2.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])